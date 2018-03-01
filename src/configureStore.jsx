import { createStore, combineReducers } from 'redux';
import {IMAGE_ACTIONS, STATUS} from './actions'


const images = (state = [], action) => {
    switch (action.type) {
        case IMAGE_ACTIONS.UPLOAD_IMAGE:
            const image = {
                name: action.file.name,
                file: action.file,
                hash: action.hash,
                s3Url: null,
                upload_status: STATUS.STARTED,
                classify_status: STATUS.NOT_STARTED,
                labels: []
            }
            return [...state, image];
        case IMAGE_ACTIONS.UPLOAD_COMPLETED:
            return state.map((image, index) => {
                if (image.upload_status === STATUS.STARTED && image.hash === action.hash) {
                    return {...image, upload_status: STATUS.COMPLETED, s3Url: action.s3Url}
                }
                return image;
            });
        case IMAGE_ACTIONS.CLASSIFY_IMAGE:
            return state.map((image, index) => {
                if (image.upload_status === STATUS.COMPLETED && image.hash === action.hash) {
                    return {...image, classify_status: STATUS.STARTED}
                }
                return image;
            });
        case IMAGE_ACTIONS.CLASSIFY_COMPLETED:
            return state.map((image, index) => {
                if (image.classify_status === STATUS.STARTED && image.hash === action.hash) {
                    return {...image, classify_status: STATUS.COMPLETED}
                }
                return image;
            });
        default:
            return state;

    }
}

const rootReducer = combineReducers({
    images
})

export default (initialState) => (
    createStore(
        rootReducer,
        initialState,
        window.devToolsExtension ? window.devToolsExtension() : undefined
    )
)
