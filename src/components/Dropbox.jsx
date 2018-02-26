
import React from 'react'
import Dropzone from 'react-dropzone'
import { connect } from 'react-redux';
import {IMAGE_ACTIONS, uploadFiles} from '../actions';
import uuid4 from 'uuid4';
import AWS from 'aws-sdk';

const style = {
    textAlign: 'center',
    height: 100,
    margin: 20,
    borderStyle: 'dashed',
    borderWidth: 2,
    borderColor: 'lightgrey',
    fontSize: 32,
    fontFamily: 'Arial, Helvetica, sans-serif',
    color: 'lightgrey',
    display: 'flex',
    justifyContent: 'center',
    flexDirection: 'column'
};

const styleOverlay = {

}

const Dropbox = (props) => {
    return (
        <section>
            <div className="dropzone">
                <Dropzone onDrop={props.onDrop} style={style}>
                    Drag n Drop Images
                </Dropzone>
            </div>
        </section>
    )
}

const mapStateToProps = state => {
    return {};
}

const mapDispatchToProps = dispatch => {
    return {
        onDrop: uploadFiles(dispatch)
    };
}

export default connect(mapStateToProps, mapDispatchToProps)(Dropbox);
