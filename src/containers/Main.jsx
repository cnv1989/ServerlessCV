import React from 'react';

import {Tabs, Tab} from 'material-ui/Tabs';

import Dropzone from 'react-dropzone'
import Dropbox from '../components/Dropbox';
import Stages from '../components/Stages';

export default () => (
	<div>
        <Dropbox />
        <Stages />
    </div>
)
