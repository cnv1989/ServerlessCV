import uuid4 from 'uuid4';
import AWS from 'aws-sdk';
import StackOutput from '../StackOutput';
import LambdaOutput from '../LambdaOutput';
import SHA256 from 'crypto-js/sha256';


const getValue = (Output, key) => (
    Output['Stacks'][0]['Outputs'].find(output => output.OutputKey === key).OutputValue
)

const BucketName = getValue(StackOutput, 'ImageStore');
const IdentityPoolId = getValue(StackOutput, 'IdentityPool');
const Region = 'us-west-2';
const APIUrlPrefix = getValue(LambdaOutput, 'ProcessImageApi');

const API_URL = 'https:\/\/' + APIUrlPrefix + '.execute-api.' + Region + '.amazonaws.com/Prod/process_image';
// const API_URL = 'http:\/\/127.0.0.1:3000/process_image';

const generateImageUrl = imageName => ('https:\/\/' + BucketName + '.s3.amazonaws.com/' + imageName);

const getHashName = (file, hash) => {
    const ext = file.name.split('.').pop();
    return hash + '.' + ext;
}

AWS.config.region = Region;

AWS.config.credentials = new AWS.CognitoIdentityCredentials({
    IdentityPoolId: IdentityPoolId
});

var S3 = new AWS.S3({
    apiVersion: '2006-03-01',
    params: {Bucket: BucketName}
});

export const IMAGE_ACTIONS = {
    UPLOAD_IMAGE: 'UPLOAD_IMAGE',
    UPLOAD_COMPLETED: 'UPLOAD_COMPLETED',
    RESIZE_IMAGE: 'RESIZE_IMAGE',
    RESIZE_COMPLETED: 'RESIZE_COMPLETED',
    CLASSIFY_IMAGE: 'CLASSIFY_IMAGE',
    CLASSIFY_COMPLETED: 'CLASSIFY_COMPLETED',
    ERROR: 'ERROR'
};

export const STATUS = {
    NOT_STARTED: 0,
    STARTED: 1,
    COMPLETED: 2
};

const generatePayload = (filename) => ({
    method: 'POST',
    mode: 'cors',
    headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        image_name: filename
    })
});

const loadImage = (file, hash, dispatch) => new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve({img, file});
    img.onerror = () => reject(new Error("Unable to load image."));
    img.src = file.preview;
    dispatch({
        type: IMAGE_ACTIONS.UPLOAD_IMAGE,
        file: file,
        name: file.name,
        hash: hash,
        s3Url: null
    });
});

const checkImage = ({img, file}) => new Promise((resolve, reject) => {
    if (img.width < 608 || img.height < 608) {
        reject(new Error("Image should have minimum dimensions of 608 x 608. Uploaded image is " + img.width + "x" + img.height + "."));
    } else {
        resolve({file});
    }
});

const uploadFileToS3 = ({file, hash, dispatch}) => new Promise((resolve, reject) => {
    const params = {
        Key: getHashName(file, hash),
        Body: file
    };

    S3.upload(params, (err, data) => {
        if (err) {
            reject(err);
        } else {
            resolve({file, data});
        }
    })

});

const classifyImage = ({file, hash, data, dispatch}) => {
    dispatch({
        type: IMAGE_ACTIONS.UPLOAD_COMPLETED,
        hash: hash,
        s3Url: data.Location
    });
    const imageUrl = data.Location;
    dispatch({
        type: IMAGE_ACTIONS.CLASSIFY_IMAGE,
        hash: hash
    });
    return fetch(API_URL, generatePayload(getHashName(file, hash)));
};

export const uploadFiles = dispatch => {

    return files => {
        files.map((file, index) => {
            const hash = uuid4();

            const errorHandler = (error) => {
                dispatch({
                    hash: hash,
                    type: IMAGE_ACTIONS.ERROR,
                    error: error
                });
            }

            loadImage(file, hash, dispatch)
            .then(checkImage)
            .then( data => {
                return uploadFileToS3({...data, hash, dispatch});
            })
            .then((data) => {
                return classifyImage({...data, hash, dispatch});
            }).then((response) => {
                if (!response.ok) {
                    throw new Error("Out of lambda memory. Try again!");
                }
                return response.json();
            }).then((resp) => {

                dispatch({
                    type: IMAGE_ACTIONS.CLASSIFY_COMPLETED,
                    hash: hash,
                    updateImageUrl: generateImageUrl(resp.classified_image_name)
                });
            })
            .catch(errorHandler);
        });
    }
}
