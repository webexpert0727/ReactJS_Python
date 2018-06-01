var React = require('react');
var createReactClass = require('create-react-class');
var _ = require('lodash');
var $ = require('jquery');
var withRouter = require('react-router-dom').withRouter;
var ReactCSSTransitionGroup = require('react-addons-css-transition-group');


var AnalysisPage = createReactClass({

    render: function () {
        return (
            <div className="container">
                <div className="row" style={{marginTop:'0px'}}>
                    <div className="col-xs-10 col-xs-offset-1 col-sm-6 col-sm-offset-3">
                        <h1 className="text-center">Analysis page coming soon!</h1>
                    </div>
                </div>
            </div>
        );
    }
});


module.exports = withRouter(AnalysisPage);
