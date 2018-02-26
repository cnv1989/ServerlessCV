import React from "react";
import getMuiTheme from 'material-ui/styles/getMuiTheme';
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';
import Share from 'material-ui/svg-icons/social/share';
import IconButton from 'material-ui/IconButton';
import AppBar from 'material-ui/AppBar';

import Main from "./Main";

const muiTheme = getMuiTheme();

export default () => (
    <MuiThemeProvider muiTheme={muiTheme}>
        <div>
            <AppBar title="Deep Neural Networks" iconElementLeft={<IconButton><Share /></IconButton>}/>
            <Main />
        </div>
    </MuiThemeProvider>
)
