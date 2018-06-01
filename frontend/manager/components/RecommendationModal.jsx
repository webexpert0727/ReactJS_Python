var React = require('react');
var createReactClass = require('create-react-class');
var _ = require('lodash');
var $ = require('jquery');
var ReactDOM = require('react-dom');
var Link = require('react-router-dom').Link;
var withRouter = require('react-router-dom').withRouter;

var moment = require('moment');
var DataTable = require('datatables.net-bs');
var swal = require('sweetalert');
require('sweetalert/dist/sweetalert.css');
require('datatables.net-bs/css/dataTables.bootstrap.css');


var RecommendationModal = createReactClass({

    render: function () {
        var actions = this.props.recommendation.actions;
        var statistics = this.props.recommendation.statistics;

        return (
            <div className="modal fade" id="viewPrediction" role="dialog"
                 aria-labelledby="myModalLabel"
                 aria-hidden="true">
                <div className="modal-dialog" style={{width: '90%'}}>
                    <div className="modal-content">
                        <div className="modal-header">
                            <button type="button" className="close" data-dismiss="modal" aria-label="Close"><span
                                aria-hidden="true">&times;</span></button>
                            <h1 className="modal-title text-center">{moment().format('MMMM')}'s Recommendation</h1>
                        </div>
                        <div className="modal-body">
                            <div className="row">
                                <div className="col-xs-12 col-md-12">
                                    <div className="row">
                                        <div className="col-xs-4 col-md-4">
                                            <div className="panel" style={{backgroundColor: '#4CAEE2'}}>
                                                <div className="panel-heading">
                                                    <div className="row">
                                                        <div className="col-xs-6">
                                                            <div style={{color: '#FFFFFF', paddingBottom: '10px'}}>
                                                                ADVERTISEMENTS
                                                            </div>
                                                            <img style={{width: '65px', marginLeft: '10px'}}
                                                                 src={STATIC + "images/adwords_logo.png"}
                                                                 className="img"
                                                                 alt="Responsive image"/>
                                                        </div>
                                                        <div className="col-xs-6 text-right">
                                                            <div style={{
                                                                fontSize: '80px',
                                                                color: '#FFFFFF'
                                                            }}>{actions.adwords_cost.toFixed(0)}</div>

                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="col-xs-4 col-md-4">
                                            <div className="panel" style={{backgroundColor: '#4359A3'}}>
                                                <div className="panel-heading">
                                                    <div className="row">
                                                        <div className="col-xs-6">
                                                            <div style={{color: '#FFFFFF', paddingBottom: '10px'}}>
                                                                ADVERTISEMENTS
                                                            </div>
                                                            <i style={{marginLeft: '10px', color: '#FFFFFF'}}
                                                               className="fa fa-facebook fa-4x"></i>
                                                        </div>
                                                        <div className="col-xs-6 text-right">
                                                            <div style={{
                                                                fontSize: '80px',
                                                                color: '#FFFFFF'
                                                            }}>{actions.facebook_advertising_cost.toFixed(0)}</div>

                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="col-xs-4 col-md-4">
                                            <div className="panel" style={{backgroundColor: '#B9A258'}}>
                                                <div className="panel-heading">
                                                    <div className="row">
                                                        <div className="col-xs-6">
                                                            <div style={{color: '#FFFFFF', paddingBottom: '10px'}}>
                                                                COFFEES
                                                                INTRODUCED
                                                            </div>
                                                            <i style={{marginLeft: '10px', color: '#FFFFFF'}}
                                                               className="fa fa-coffee fa-4x"></i>
                                                        </div>
                                                        <div className="col-xs-6 text-right">
                                                            <div style={{
                                                                fontSize: '80px',
                                                                color: '#FFFFFF'
                                                            }}>{actions.new_coffees.toFixed(0)}</div>

                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="col-xs-4 col-md-4">
                                            <div className="panel" style={{backgroundColor: '#72BBB0'}}>
                                                <div className="panel-heading">
                                                    <div className="row">
                                                        <div className="col-xs-6">
                                                            <div style={{color: '#FFFFFF', paddingBottom: '10px'}}>BLOG
                                                                ARTICLES
                                                            </div>
                                                            <i style={{marginLeft: '10px', color: '#FFFFFF'}}
                                                               className="fa fa-wordpress fa-4x"></i>
                                                        </div>
                                                        <div className="col-xs-6 text-right">
                                                            <div style={{
                                                                fontSize: '80px',
                                                                color: '#FFFFFF'
                                                            }}>{actions.blog_posts.toFixed(0)}</div>

                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="col-xs-4 col-md-4">
                                            <div className="panel" style={{backgroundColor: '#2D9199'}}>
                                                <div className="panel-heading">
                                                    <div className="row">
                                                        <div className="col-xs-6">
                                                            <div style={{color: '#FFFFFF', paddingBottom: '10px'}}>EMAIL
                                                                CAMPAIGNS
                                                            </div>
                                                            <i style={{marginLeft: '10px', color: '#FFFFFF'}}
                                                               className="fa fa-envelope fa-4x"></i>
                                                        </div>
                                                        <div className="col-xs-6 text-right">
                                                            <div style={{
                                                                fontSize: '80px',
                                                                color: '#FFFFFF'
                                                            }}>{actions.email_campaigns.toFixed(0)}</div>

                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="col-xs-4 col-md-4">
                                            <div className="panel" style={{backgroundColor: '#F3776E'}}>
                                                <div className="panel-heading">
                                                    <div className="row">
                                                        <div className="col-xs-6">
                                                            <div style={{color: '#FFFFFF', paddingBottom: '10px'}}>
                                                                ROADSHOWS
                                                            </div>
                                                            <i style={{marginLeft: '10px', color: '#FFFFFF'}}
                                                               className="fa fa-shopping-cart fa-4x"></i>
                                                        </div>
                                                        <div className="col-xs-6 text-right">
                                                            <div style={{
                                                                fontSize: '80px',
                                                                color: '#FFFFFF'
                                                            }}>{actions.roadshows.toFixed(0)}</div>

                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="row">
                                        <div style={{textAlign: 'center'}}>
                                            <span style={{fontSize:'1.2em'}}>Estimated demand:</span><span style={{fontSize:'1.8em'}}> {statistics.expected_demand.toFixed(2)}%</span>
                                        </div>
                                        <div style={{textAlign: 'center'}}>
                                            <span style={{fontSize:'1.2em'}}>Demand actualising:</span><span style={{fontSize:'1.8em'}}> {statistics.demand_actualising.toFixed(2)}%</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                        </div>
                        {/*<div className="modal-footer">*/}
                        {/*<button className="btn btn-primary btn-sm" type="submit" style={{backgroundColor: '#9c1209'}}>*/}
                        {/*Reset*/}
                        {/*</button>*/}
                        {/*<button className="btn btn-primary btn-sm" type="submit">Save</button>*/}
                        {/*</div>*/}
                    </div>
                </div>
            </div>
        );
    }
});


module.exports = withRouter(RecommendationModal);
