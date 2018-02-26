import React from 'react';
import {
    Step,
    Stepper,
    StepLabel,
    StepContent,
} from 'material-ui/Stepper';
import Divider from 'material-ui/Divider';
import RaisedButton from 'material-ui/RaisedButton';
import FlatButton from 'material-ui/FlatButton';
import Paper from 'material-ui/Paper';
import CircularProgress from 'material-ui/CircularProgress';
import CloudDone from 'material-ui/svg-icons/file/cloud-done';
import Transform from 'material-ui/svg-icons/image/transform';
import Search from 'material-ui/svg-icons/action/search';
import AssignmentTurnedIn from 'material-ui/svg-icons/action/assignment-turned-in';

import {lightGreen600} from 'material-ui/styles/colors';
import { connect } from 'react-redux';

import {STATUS} from '../actions';

const ImageThumbnail = ({image, status, stage}) => {
    const stageToIcon = {
        'uploading': (
            <CloudDone color={lightGreen600} />
        ),
        'resizing': (
            <Transform color={lightGreen600} />
        ),
        'classifying': (
            <Search color={lightGreen600} />
        ),
        'results': (
            <AssignmentTurnedIn color={lightGreen600} />
        )
    }
    const icon = stageToIcon[stage];
    return (
        <div>
            <div style={{
                margin: 10
            }}>
                <span style={{padding: 10, height: 30}}>{image.name}</span>
                <span style={{textAlign: 'center'}}>
                    {status === STATUS.COMPLETED ? icon : (
                        <CircularProgress size={20}/>
                    )}
                </span>
            </div>
            {stage === 'uploading' ? (
                <Paper style={
                    {
                        height: 100,
                        margin: 10,
                        textAlign: 'center',
                        display: 'inline-block',
                    }
                }>
                    <img src={image.file.preview} style={{height: 100}}/>
                </Paper>
            ):
            null}
            <Divider />
        </div>
    );
}

const Stage = (props) => (
    <div>
        {props.images.map((image, index) => (
            <ImageThumbnail key={index} image={image} status={image[props.status]} stage={props.stage}/>
        ))}
    </div>
);

const ImageProcessingStages = props => {
    return (
        <div>
            <Stepper orientation="vertical">
                <Step active={true}>
                    <StepLabel><h3>Uploading Image(s)</h3></StepLabel>
                    <StepContent>
                        <Stage images={props.images} status='upload_status' stage='uploading'/>
                    </StepContent>
                </Step>
                <Step active={true}>
                    <StepLabel><h3>Resizing Image(s)</h3></StepLabel>
                    <StepContent>
                        <Stage images={props.images.filter(image => image.upload_status === STATUS.COMPLETED)} status='resize_status' stage='resizing'/>
                    </StepContent>
                </Step>
                <Step active={true}>
                    <StepLabel><h3>Classifying Image(s)</h3></StepLabel>
                    <StepContent>
                        <Stage images={props.images.filter(image => image.resize_status === STATUS.COMPLETED)} status='classify_status' stage='classifying'/>
                    </StepContent>
                </Step>
                <Step active={true}>
                    <StepLabel><h3>Results</h3></StepLabel>
                    <StepContent>
                        <Stage images={props.images.filter(image => image.classify_status === STATUS.COMPLETED)} status='completed' stage='results'/>
                    </StepContent>
                </Step>
            </Stepper>
        </div>
    );
}


const mapStateToProps = state => {
    return state;
}

const mapDispatchToProps = dispatch => {
    return {};
}


export default connect(mapStateToProps, mapDispatchToProps)(ImageProcessingStages);
