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

API_URL = 'https:\/\/{0}.execute-api.{1}.amazonaws.com/Prod/process_image'.format(APIUrlPrefix, Region)

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
    CLASSIFY_COMPLETED: 'CLASSIFY_COMPLETED'
};

export const STATUS = {
    NOT_STARTED: 0,
    STARTED: 1,
    COMPLETED: 2
};


export const uploadFiles = dispatch => {
    const fetchPayload = (filename) => ({
        method: 'POST',
        mode: 'no-cors',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            image_name: filename
        })
    });


    return files => {
        files.map((file, index) => {
            const hash = uuid4();

            dispatch({
                type: IMAGE_ACTIONS.UPLOAD_IMAGE,
                file: file,
                name: file.name,
                hash: hash,
                s3Url: null
            });

            const params = {
                Key: file.name,
                Body: file
            };

            const s3UploadPromise = S3.upload(params).promise();

            s3UploadPromise.then( data => {
                dispatch({
                    type: IMAGE_ACTIONS.UPLOAD_COMPLETED,
                    hash: hash,
                    s3Url: data.Location
                });
                return data;

            }).then( (upload_response) => {
                const imageUrl = upload_response.Location;
                dispatch({
                    type: IMAGE_ACTIONS.CLASSIFY_IMAGE,
                    hash: hash
                });
                fetch(API_URL, fetchPayload(file.name)).then((res) => {
                    return res.text();
                }).then((resp) => {
                    const updateImageUrl = imageUrl.replace(file.name, 'classified-' + file.name);
                    console.log(updateImageUrl)

                    dispatch({
                        type: IMAGE_ACTIONS.CLASSIFY_COMPLETED,
                        hash: hash,
                        updateImageUrl: updateImageUrl
                    });
                })
            });
        });
    }
}
