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


var ReportCardModal = createReactClass({

    saveActions: function () {
        var advertisements = this.refs.adwords.value;
        var facebook = this.refs.facebook.value;
        var coffeesintroduced = this.refs.coffeesintroduced.value;
        var blogarticles = this.refs.blogarticles.value;
        var emailcampaigns = this.refs.emailcampaigns.value;
        var roadshows = this.refs.roadshows.value;

        var report_id = this.props.report.report_card.report_id;

        console.log(advertisements);
        console.log(facebook);
        console.log(coffeesintroduced);
        console.log(blogarticles);
        console.log(emailcampaigns);
        console.log(roadshows);
        console.log(report_id);

        var csrftoken = '';
        var cookies = document.cookie.split(';');
        _.map(cookies, function (cookie) {
            var keyValue = cookie.split('=');
            if (keyValue[0].trim() == 'csrftoken') {
                csrftoken = keyValue[1];
            }
            ;
        });

        var data = {
            report_id: report_id,
            facebook_advertising_cost: facebook,
            blog_posts: blogarticles,
            email_campaigns: emailcampaigns,
            adwords_cost: advertisements,
            roadshows: roadshows,
            new_coffees: coffeesintroduced,
        }

        var ajax = $.ajax({
            url: '/manager/api/updateReportCard',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            },
            method: 'POST',
            data: JSON.stringify(data),
            dataType: 'json',
            jsonp: false,
            context: this,
            success: function (res) {
                console.log(res);
                if (res.status == 200) {
                    swal({
                            title: "Success!",
                            text: res.message,
                            type: "success",
                            confirmButtonColor: '#DAA62A'
                        });
                    // window.alert(res.message)
                    $('#viewReportCard' + this.props.month.format('MMMM')).modal('toggle');
                } else {
                    swal({
                            title: 'Error',
                            text: res.error_message,
                            type: 'warning',
                            confirmButtonColor: '#DAA62A'
                        });
                    // window.alert(res.error_message);
                }
            },
            error: function (e) {
                console.log(e);
            }
        });

    },

    render: function () {

        var actions = this.props.report.report_card.actions;
        var month = moment(this.props.month);
        return (
            <div className="modal fade" id={"viewReportCard" + this.props.month.format('MMMM')} aria-hidden="true">
                <div className="modal-dialog" style={{width: '90%'}}>
                    <div className="modal-content">
                        <div className="modal-header">
                            <div className="row">
                                <div className="col-xs-12 col-md-12">
                                    <button type="button" className="close" data-dismiss="modal"
                                            aria-label="Close"><span
                                        aria-hidden="true">&times;</span></button>
                                    <h1 className="text-center">{this.props.month.format('MMMM')}'s Report
                                        Card</h1>
                                </div>
                            </div>
                        </div>
                        <div className="modal-body">
                            <div className="row">
                                <div className="col-xs-12 col-md-12">
                                    <p className="text-center" style={{fontSize: '1.7em'}}>You have <span style={{fontSize: '1.4em'}}>{this.props.report.report_card.new_signups} new sign ups</span>. There were <span style={{fontSize: '1.3em'}}>{this.props.report.report_card.orders} orders </span> for the month.</p>
                                    <p className="text-center" style={{fontSize: '1.7em'}}> Churn was <span  style={{fontSize: '1.4em'}}>{this.props.report.report_card.churn}</span>. There were <span style={{fontSize: '1.3em'}}>{this.props.report.report_card.active_customers}</span> active customers.</p>
                                    <p className="text-center" style={{fontSize: '1.3em'}}>Please key in the values for each category for this month.</p>
                                </div>
                            </div>
                            <div className="row">
                                <div className="col-xs-12 col-md-12">
                                    <div className="row">
                                        <div className="col-xs-12 col-md-12">
                                            <div className="row">
                                                <div className="col-xs-12">
                                                    <div className="row">
                                                        <div className="col-xs-4 col-md-4">
                                                            <div className="panel" style={{backgroundColor: '#4CAEE2'}}>
                                                                <div className="panel-heading">
                                                                    <div className="row">
                                                                        <div className="col-xs-12"
                                                                             style={{
                                                                                 color: '#FFFFFF',
                                                                                 paddingBottom: '10px'
                                                                             }}>
                                                                            GOOGLE ADWORDS
                                                                        </div>
                                                                    </div>
                                                                    <div className="row">
                                                                        <div className="col-xs-6">
                                                                            <img style={{
                                                                                width: '65px',
                                                                                marginLeft: '10px'
                                                                            }}
                                                                                 src={STATIC + "images/adwords_logo.png"}
                                                                                 className="img"
                                                                                 alt="Responsive image"/>

                                                                        </div>
                                                                        <div className="col-xs-6 text-right">
                                                                            <div className="row">
                                                                                <div className="col-xs-12 ">
                                                                                    <input type="text"
                                                                                           className="form-control"
                                                                                           id="adwords" ref="adwords"
                                                                                           style={{fontSize: '1.3em'}}
                                                                                           defaultValue={actions.adwords_cost}/>
                                                                                </div>
                                                                                {/*<div className="row">*/}
                                                                                    {/*<div className="col-xs-12" style={{*/}
                                                                                        {/*color: 'rgb(19, 243, 19)',*/}
                                                                                        {/*fontSize: '1.2em',*/}
                                                                                        {/*paddingRight: '10%'*/}
                                                                                    {/*}}>*/}

                                                                                        {/*+3.2% from {month.format("MMM 'YY")}*/}
                                                                                    {/*</div>*/}
                                                                                {/*</div>*/}
                                                                            </div>

                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                        <div className="col-xs-4 col-md-4">
                                                            <div className="panel" style={{backgroundColor: '#4359A3'}}>
                                                                <div className="panel-heading">
                                                                    <div className="row">
                                                                        <div className="col-xs-12"
                                                                             style={{
                                                                                 color: '#FFFFFF',
                                                                                 paddingBottom: '10px'
                                                                             }}>
                                                                            FACEBOOK ADS
                                                                        </div>
                                                                    </div>
                                                                    <div className="row">
                                                                        <div className="col-xs-6">
                                                                            <i style={{
                                                                                marginLeft: '10px',
                                                                                color: '#FFFFFF'
                                                                            }}
                                                                               className="fa fa-facebook fa-4x"></i>
                                                                        </div>
                                                                        <div className="col-xs-6 text-right">
                                                                            <div className="row">
                                                                                <div className="col-xs-12 ">
                                                                                    <input type="text"
                                                                                           className="form-control"
                                                                                           id="facebook" ref="facebook"
                                                                                           style={{fontSize: '1.3em'}}
                                                                                           defaultValue={actions.facebook_advertising_cost}/>
                                                                                </div>
                                                                                {/*<div className="row">*/}
                                                                                    {/*<div className="col-xs-12" style={{*/}
                                                                                        {/*color: 'red',*/}
                                                                                        {/*fontSize: '1.2em',*/}
                                                                                        {/*paddingRight: '10%'*/}
                                                                                    {/*}}>*/}

                                                                                        {/*-2.2% from {month.format("MMM 'YY")}*/}
                                                                                    {/*</div>*/}
                                                                                {/*</div>*/}
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                        <div className="col-xs-4 col-md-4">
                                                            <div className="panel" style={{backgroundColor: '#B9A258'}}>
                                                                <div className="panel-heading">
                                                                    <div className="row">

                                                                        <div className="col-xs-12"
                                                                             style={{
                                                                                 color: '#FFFFFF',
                                                                                 paddingBottom: '10px'
                                                                             }}>
                                                                            NEW COFFEES
                                                                        </div>
                                                                    </div>
                                                                    <div className="row">
                                                                        <div className="col-xs-6">

                                                                            <i style={{color: '#FFFFFF'}}
                                                                               className="fa fa-coffee fa-4x"></i>
                                                                        </div>
                                                                        <div className="col-xs-6 text-right">
                                                                            <div className="row">
                                                                                <div className="col-xs-12 ">
                                                                                    <input type="text"
                                                                                           className="form-control"
                                                                                           id="coffeeintroduced"
                                                                                           ref="coffeesintroduced"
                                                                                           style={{fontSize: '1.3em'}}
                                                                                           defaultValue={actions.new_coffees}/>
                                                                                </div>
                                                                                {/*<div className="row">*/}
                                                                                    {/*<div className="col-xs-12" style={{*/}
                                                                                        {/*color: 'rgb(19, 243, 19)',*/}
                                                                                        {/*fontSize: '1.2em',*/}
                                                                                        {/*paddingRight: '10%'*/}
                                                                                    {/*}}>*/}

                                                                                        {/*+3.2% from {month.format("MMM 'YY")}*/}
                                                                                    {/*</div>*/}
                                                                                {/*</div>*/}
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div className="row">
                                                        <div className="col-xs-4 col-md-4">
                                                            <div className="panel" style={{backgroundColor: '#72BBB0'}}>
                                                                <div className="panel-heading">
                                                                    <div className="row">
                                                                        <div className="col-xs-12"
                                                                             style={{
                                                                                 color: '#FFFFFF',
                                                                                 paddingBottom: '10px'
                                                                             }}>BLOG
                                                                            ARTICLES
                                                                        </div>
                                                                    </div>
                                                                    <div className="row">
                                                                        <div className="col-xs-6">

                                                                            <i style={{
                                                                                marginLeft: '10px',
                                                                                color: '#FFFFFF'
                                                                            }}
                                                                               className="fa fa-wordpress fa-4x"></i>
                                                                        </div>
                                                                        <div className="col-xs-6 text-right">
                                                                            <div className="row">
                                                                                <div className="col-xs-12 ">
                                                                                    <input type="text"
                                                                                           className="form-control"
                                                                                           id="blogarticles"
                                                                                           ref="blogarticles"
                                                                                           style={{fontSize: '1.3em'}}
                                                                                           defaultValue={actions.blog_posts}/>
                                                                                </div>
                                                                                {/*<div className="row">*/}
                                                                                    {/*<div className="col-xs-12" style={{*/}
                                                                                        {/*color: 'rgb(19, 243, 19)',*/}
                                                                                        {/*fontSize: '1.2em',*/}
                                                                                        {/*paddingRight: '10%'*/}
                                                                                    {/*}}>*/}

                                                                                        {/*+3.2% from {month.format("MMM 'YY")}*/}
                                                                                    {/*</div>*/}
                                                                                {/*</div>*/}
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                        <div className="col-xs-4 col-md-4">
                                                            <div className="panel" style={{backgroundColor: '#2D9199'}}>
                                                                <div className="panel-heading">
                                                                    <div className="row">
                                                                        <div className="col-xs-12"
                                                                             style={{
                                                                                 color: '#FFFFFF',
                                                                                 paddingBottom: '10px'
                                                                             }}>EMAIL
                                                                            CAMPAIGNS
                                                                        </div>
                                                                    </div>
                                                                    <div className="row">
                                                                        <div className="col-xs-6">

                                                                            <i style={{
                                                                                marginLeft: '10px',
                                                                                color: '#FFFFFF'
                                                                            }}
                                                                               className="fa fa-envelope fa-4x"></i>
                                                                        </div>
                                                                        <div className="col-xs-6 text-right">
                                                                            <div className="row">
                                                                                <div className="col-xs-12 ">
                                                                                    <input type="text"
                                                                                           className="form-control"
                                                                                           id="emailcampaigns"
                                                                                           ref="emailcampaigns"
                                                                                           style={{fontSize: '1.3em'}}
                                                                                           defaultValue={actions.email_campaigns}/>
                                                                                </div>
                                                                                {/*<div className="row">*/}
                                                                                    {/*<div className="col-xs-12" style={{*/}
                                                                                        {/*color: 'rgb(19, 243, 19)',*/}
                                                                                        {/*fontSize: '1.2em',*/}
                                                                                        {/*paddingRight: '10%'*/}
                                                                                    {/*}}>*/}

                                                                                        {/*+3.2% from {month.format("MMM 'YY")}*/}
                                                                                    {/*</div>*/}
                                                                                {/*</div>*/}
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                        <div className="col-xs-4 col-md-4">
                                                            <div className="panel" style={{backgroundColor: '#F3776E'}}>
                                                                <div className="panel-heading">
                                                                    <div className="row">
                                                                        <div className="col-xs-12"
                                                                             style={{
                                                                                 color: '#FFFFFF',
                                                                                 paddingBottom: '10px'
                                                                             }}>
                                                                            ROADSHOWS
                                                                        </div>
                                                                    </div>
                                                                    <div className="row">
                                                                        <div className="col-xs-6">
                                                                            <i style={{
                                                                                marginLeft: '10px',
                                                                                color: '#FFFFFF'
                                                                            }}
                                                                               className="fa fa-shopping-cart fa-4x"></i>
                                                                        </div>
                                                                        <div className="col-xs-6 text-right">
                                                                            <div className="row">
                                                                                <div className="col-xs-12 ">
                                                                                    <input type="text"
                                                                                           className="form-control"
                                                                                           id="roadshows"
                                                                                           ref="roadshows"
                                                                                           style={{fontSize: '1.3em'}}
                                                                                           defaultValue={actions.roadshows}/>
                                                                                </div>
                                                                                {/*<div className="row">*/}
                                                                                    {/*<div className="col-xs-12" style={{*/}
                                                                                        {/*color: 'rgb(19, 243, 19)',*/}
                                                                                        {/*fontSize: '1.2em',*/}
                                                                                        {/*paddingRight: '10%'*/}
                                                                                    {/*}}>*/}

                                                                                        {/*+3.2% from {month.format("MMM 'YY")}*/}
                                                                                    {/*</div>*/}
                                                                                {/*</div>*/}
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                        </div>
                        <div className="modal-footer" style={{textAlign: 'center'}}>
                            <button className="btn btn-primary btn-lg" style={{width: '50%'}}
                                    onClick={this.saveActions}>Save
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
});


module.exports = withRouter(ReportCardModal);
