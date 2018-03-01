import uuid4 from 'uuid4';
import AWS from 'aws-sdk';
import StackOutput from '../StackOutput';
import SHA256 from 'crypto-js/sha256';


const getValue = key => (
    StackOutput['Stacks'][0]['Outputs'].find(output => output.OutputKey === key).OutputValue
)

const BucketName = getValue('ImageStore')
const IdentityPoolId = getValue('IdentityPool') // 'us-west-2:7fea0e16-fe5c-4724-aa9b-cdf844591e6f'
const Region = 'us-west-2'

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
                console.log(upload_response);
                dispatch({
                    type: IMAGE_ACTIONS.CLASSIFY_IMAGE,
                    hash: hash
                });
                fetch('https://hp4t5usv1a.execute-api.us-west-2.amazonaws.com/Stage/image/process', {
                    method: 'POST',
                    mode: 'no-cors',
                    body: JSON.stringify({
                        image_name: file.name
                    })
                }).then((res) => (res.json())).then( (res_data) => {
                    console.log(res_data);
                    dispatch({
                        type: IMAGE_ACTIONS.CLASSIFY_COMPLETED,
                        hash: hash
                    });
                })
            });
        });
    }
}
