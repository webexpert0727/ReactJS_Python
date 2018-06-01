var React = require('react');
var createReactClass = require('create-react-class');
var _ = require('lodash');
var $ = require('jquery');
var withRouter = require('react-router-dom').withRouter;
var ReactCSSTransitionGroup = require('react-addons-css-transition-group');
var OrderModal = require('./OrderModal');
var swal = require('sweetalert');
require('sweetalert/dist/sweetalert.css');

var moment = require('moment');
var DataTable = require('datatables.net-bs');
require('datatables.net-bs/css/dataTables.bootstrap.css');


const ReactHighcharts = require('react-highcharts');


var Select2 = require('react-select2-wrapper');
require('select2/dist/css/select2.min.css');


var MarketingPage = createReactClass({
    getInitialState: function () {
        return {mailingLists: [], campaigns: [], loading: {mailinglist: true, campaignresults: true}};
    },
    componentWillMount: function () {
        this.getMailingLists();
        this.getCampaigns();
    },
    getMailingLists: function () {
        this.setState({loading:{mailinglist: true}});

        var csrftoken = '';
        var cookies = document.cookie.split(';');
        _.map(cookies, function (cookie) {
            var keyValue = cookie.split('=');
            if (keyValue[0].trim() == 'csrftoken') {
                csrftoken = keyValue[1];
            }
            ;
        });

        $.ajax({
            url: '/manager/api/getMailchimpLists?count=' + '99999999' + '&offset=0',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            },
            method: 'GET',
            dataType: 'json',
            context: this,
            success: function (res) {
                console.log(res);
                var mailingLists = res.lists;
                _.reverse(mailingLists);
                this.setState({mailingLists: mailingLists, loading: {mailinglist: false}});
            }
        });
    },
    getCampaigns: function () {
        var csrftoken = '';
        var cookies = document.cookie.split(';');
        _.map(cookies, function (cookie) {
            var keyValue = cookie.split('=');
            if (keyValue[0].trim() == 'csrftoken') {
                csrftoken = keyValue[1];
            }
            ;
        });
        $.ajax({
            url: '/manager/api/getMailchimpCampaigns?count=' + '99999999' + '&offset=0',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            },
            method: 'GET',
            dataType: 'json',
            context: this,
            success: function (res) {
                console.log(res);
                var campaigns = res.campaigns;
                this.setState({campaigns: campaigns, loading: {campaignresults: false}});

            }
        });
    },
    render: function () {

        if (this.state.loading.mailinglist || this.state.loading.campaignresult) {
            return (
                <div className="container">
                    <div className="row" style={{marginTop: '0px', marginBottom: '20px'}}>
                        <div className="col-xs-10 col-xs-offset-1 col-sm-6 col-sm-offset-3">
                            <h1 className="text-center">Personalize Your Campaigns!</h1>
                        </div>
                    </div>
                    <div style={{textAlign: 'center', marginTop: '130px'}}><i className="fa fa-spinner fa-spin fa-3x"/>
                    </div>
                </div>
            )
        }

        return (
            <div>
                <MailingListModal getMailingLists={this.getMailingLists}></MailingListModal>

                <MailingListSection mailingLists={this.state.mailingLists}
                                    ></MailingListSection>
                <hr/>
                <CampaignResultsSection campaigns={this.state.campaigns}></CampaignResultsSection>
            </div>
        )
    }
});
var MailingListModal = createReactClass({

    submit: function (e) {
        e.preventDefault();
        var csrftoken = '';
        var cookies = document.cookie.split(';');
        _.map(cookies, function (cookie) {
            var keyValue = cookie.split('=');
            if (keyValue[0].trim() == 'csrftoken') {
                csrftoken = keyValue[1];
            }
            ;
        });

        var list_name = this.refs.listname.value;
        var permission_reminder = this.refs.permissionreminder.value;
        var from_name = this.refs.defaultfromname.value;
        var from_email = this.refs.defaultfromemail.value;

        var data = {
            list_name: list_name,
            permission_reminder: permission_reminder,
            from_name: from_name,
            from_email: from_email,
        };

        console.log(JSON.stringify(data));

        var ajax = $.ajax({
            url: '/manager/api/createMailchimpList/',
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
                    $('#createListModal').modal('toggle');
                    this.refs.listname.value = '';
                    this.refs.permissionreminder.value = '';
                    this.refs.defaultfromname.value = '';
                    this.refs.defaultfromemail.value = '';
                    this.props.getMailingLists();
                    swal({
                            title: "Success!",
                            text: 'Mailing list added!',
                            type: "success",
                            confirmButtonColor: '#DAA62A'
                        });
                    // window.alert('Mailing list added!');

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

        console.log(ajax);
    },
    render: function () {
        return (
            <div className="modal fade" id="createListModal" tabIndex="-1" role="dialog" aria-labelledby="myModalLabel"
                 aria-hidden="true">
                <div className="modal-dialog">
                    <div className="modal-content">
                        <div className="modal-header">
                            <button type="button" className="close" data-dismiss="modal" aria-label="Close"><span
                                aria-hidden="true">&times;</span></button>
                            <h3 className="modal-title">Create list</h3>
                        </div>
                        <div className="modal-body">
                            <form onSubmit={this.submit}>

                                <fieldset className="form-group">
                                    <label>List Name</label>
                                    <input type="text" className="form-control" ref="listname"/>
                                </fieldset>

                                <fieldset className="form-group">
                                    <label>Default From Name</label>
                                    <input type="text" className="form-control" ref="defaultfromname"/>
                                </fieldset>

                                <fieldset className="form-group">
                                    <label>Default From Email</label>
                                    <input type="text" className="form-control" ref="defaultfromemail"/>
                                </fieldset>

                                <fieldset className="form-group">
                                    <label>Permission Reminder</label>
                                    <textarea rows="2" className="form-control" ref="permissionreminder"/>
                                </fieldset>

                                <button type="submit"
                                        style={{
                                            paddingLeft: '30px',
                                            paddingRight: '30px',
                                            marginTop: '10px',
                                            width: '100%'
                                        }}
                                        className="btn btn-primary">Submit
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        )
            ;

    }
});


var MailingListSection = createReactClass({


    getInitialState: function () {
        return {listType: 'all', loading: false};
    },
    changeListType: function () {
        if (this.refs.listType)
            this.setState({listType: this.refs.listType.el[0].value});
    },

    toggleModal: function () {
        $('#createListModal').modal('toggle');
    },
    addEmailToLists: function () {

        this.setState({loading: true});
        var listType = this.refs.listType.el[0].value;
        var listid = this.refs.mailinglist.el[0].value;

        var csrftoken = '';
        var cookies = document.cookie.split(';');
        _.map(cookies, function (cookie) {
            var keyValue = cookie.split('=');
            if (keyValue[0].trim() == 'csrftoken') {
                csrftoken = keyValue[1];
            }
            ;
        });


        var url = '';
        var data = {};
        if (listType == 'all') {
            url = '/manager/api/getAllCustomers/';
        } else if (listType == 'active') {
            url = '/manager/api/getActiveCustomers';
        } else if (listType == 'inactive') {
            if (this.refs.inactivePeriod.value == -1) {
                return;
            } else {

                var inactivePeriod = this.refs.inactivePeriod.value;
                if (!inactivePeriod || isNaN(inactivePeriod)) {
                    swal({
                            title: 'Error',
                            text: 'Please enter a number for inactive period!',
                            type: 'warning',
                            confirmButtonColor: '#DAA62A'
                        });
                    // window.alert('Please enter a number for inactive period!');
                    this.setState({loading: false});
                    return;
                }

                url = '/manager/api/getInactiveCustomers';
                // data['fromdate'] = '01-09-2016';
                data['fromdate'] = moment().add(this.refs.inactivePeriod.value * -1, 'days').format('DD-MM-YYYY');
            }

        } else {
            swal({
                            title: 'Error',
                            text: 'You have to select the type of customers you want to add!',
                            type: 'warning',
                            confirmButtonColor: '#DAA62A'
                        });
            // window.alert('You have to select the type of customers you want to add!');
            this.setState({loading: false});
            return;
        }

        console.log(url);
        console.log(data);
        $.ajax({
            url: url,
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            },
            method: 'GET',
            data: data,
            dataType: 'json',
            context: this,
            success: function (res) {
                console.log(res);
                var customers = res.customers;
                var customerEmails = _.map(customers, function (customer) {
                    return customer.customer_email;
                });

                var data2 = {
                    emails: customerEmails,
                    list_id: listid
                };
                console.log(data2);
                $.ajax({
                    url: '/manager/api/addEmailsToList/',
                    beforeSend: function (xhr) {
                        xhr.setRequestHeader('X-CSRFToken', csrftoken);
                    },
                    method: 'POST',
                    data: JSON.stringify(data2),
                    dataType: 'json',
                    context: this,
                    success: function (res) {
                        console.log(res);
                        swal({
                            title: "Success!",
                            text: customers.length + ' customers added to mailing list!',
                            type: "success",
                            confirmButtonColor: '#DAA62A'
                        });
                        // window.alert(customers.length + ' customers added to mailing list!');
                        this.setState({loading: false});
                    },
                    error: function (e) {
                        console.log(e);
                    },
                });

            }
        });

    },
    render: function () {

        if (this.state.loading) {
            return (
                <div className="container">
                    <div className="row" style={{marginTop: '0px', marginBottom: '20px'}}>
                        <div className="col-xs-10 col-xs-offset-1 col-sm-6 col-sm-offset-3">
                            <h1 className="text-center">Personalize Your Campaigns!</h1>
                        </div>
                    </div>
                    <div style={{textAlign: 'center', marginTop: '10px'}}><i className="fa fa-spinner fa-spin fa-3x"/>
                    </div>
                </div>
            )
        }


        var mailingLists = this.props.mailingLists.map(function (list) {
            return {text: list.list_name, id: list.list_id};

        });
        return (
            <div className="container">
                <div className="row" style={{marginTop: '0px', marginBottom: '20px'}}>
                    <div className="col-xs-10 col-xs-offset-1 col-sm-6 col-sm-offset-3">
                        <h1 className="text-center">Personalize Your Campaigns!</h1>
                    </div>
                </div>
                <br/>
                <div className="row">
                    <div className="col-xs-12" style={{padding:'0px', textAlign:'center'}}>

                        <span style={{fontSize: '1.2em', margin: '20px'}}>Add </span>
                        <Select2 style={{width: '25%'}}
                                 ref="listType"
                                 options={{placeholder: 'Select Your Target Group', allowClear: true}}
                                 value={this.state.listType}
                                 onChange={this.changeListType}
                                 data={[
                                     {text: '', id: ''},
                                     {text: 'All customers', id: 'all'},
                                     {text: 'Active customers', id: 'active'},
                                     {text: 'Inactive customers', id: 'inactive'},
                                 ]}
                        />

                        <span style={{fontSize: '1.2em', margin: '20px'}}>to the following mailing list: </span>
                        <Select2 style={{width: '26%'}} ref="mailinglist"
                                 options={{placeholder: 'Select Mailing List', allowClear: true}}
                                 data={mailingLists}
                        />
                        <button className="btn btn-primary btn-default" onClick={this.addEmailToLists} style={{marginLeft:'10px'}}>
                            Proceed!
                        </button>
                    </div>
                </div>
                { this.state.listType == 'inactive' ?
                    <div className="row" style={{paddingTop: '10px'}}>
                        <div className="col-xs-12">
                            Pick customers who have been inactive for <input ref="inactivePeriod" defaultValue="7"
                                                                             style={{width: '25px'}}></input> days
                        </div>
                    </div>
                    : ''
                }
                <div className="row" style={{marginBottom: '20px'}}>
                    <div className="col-xs-12">
                        <h3 className="text-center">- OR -</h3>
                        <br/>
                        <button className="btn btn-default center-block"
                                onClick={this.toggleModal}>
                            <i className="fa fa-plus-circle"></i>{'\u00a0'}
                            Create New List
                        </button>
                    </div>
                </div>
            </div>
        )
    }
});
var CampaignResultsSection = createReactClass({
    getInitialState: function () {
        return {
            campaign: null,
            clickchart: {},
            openchart: {},
            purchasechart: {},
            registerchart: {},
            campaignIndex: null,
            chartsload: false,
        };
    },
    changeList: function () {
        var index = this.refs.campaign.el[0].value;

        if (!index || !this.props.campaigns) return;
        this.setState({chartsload: true});
        console.log('id', index);

        var campaigns = this.props.campaigns;
        var campaign = campaigns[index];
        var id = campaign.campaign_id;

        var csrftoken = '';
        var cookies = document.cookie.split(';');
        _.map(cookies, function (cookie) {
            var keyValue = cookie.split('=');
            if (keyValue[0].trim() == 'csrftoken') {
                csrftoken = keyValue[1];
            }
            ;
        });

        $.ajax({
            url: '/manager/api/retrieveCampaignBreakdown?campaign_id=' + id,
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            },
            method: 'GET',
            dataType: 'json',
            context: this,
            success: function (res) {
                console.log(res);
                if (res.status == 500) {
                    swal({
                            title: 'Error',
                            text: res.error_message,
                            type: 'warning',
                            confirmButtonColor: '#DAA62A'
                        });
                    // window.alert(res.error_message);
                    return;
                }
                var breakdown = res.breakdown;


                // var percentageOpened = Math.floor(opens / emails_sent * 100);
                // var percentageOpened = summary.open_rate;

                // var percentageOpened = breakdown.opened.rate;
                // var percentageNotOpened = 1 - percentageOpened;

                var percentageOpened = breakdown.opened.number;
                var percentageNotOpened = breakdown.not_opened.number;
                var openedData = [];
                if (percentageOpened == 0 && percentageNotOpened == 0) {
                    openedData = [
                        ['Not Available', 0.00000001]
                    ]
                } else {
                    openedData = [
                        ['Did not open email: ' + percentageNotOpened, percentageNotOpened],
                        ['Opened email: ' + percentageOpened, percentageOpened],
                    ]
                }
                var openchart = {
                    chart: {
                        type: 'pie',
                    },
                    colors: ['#587F6C', '#9FE5C3'],
                    title: {
                        text: 'Open Rates'
                    },
                    plotOptions: {
                        pie: {
                            size: '90%',
                            dataLabels: {
                                enabled: false
                            },
                            showInLegend: true
                        }
                    },
                    series: [{
                        type: 'pie',
                        name: 'Number of Users',
                        data: openedData
                    }]
                };


                // var percentageClicked = breakdown.opened.clicked.rate;
                // var percentageNotClicked = 1 - percentageClicked;
                var percentageClicked = breakdown.opened.clicked.number;
                var percentageNotClicked = breakdown.opened.not_clicked.number;

                var clickedData = [];
                if (percentageClicked == 0 && percentageNotClicked == 0) {
                    clickedData = [
                        ['Not Available', 0.00000001]
                    ];
                } else {
                    clickedData = [
                        ['Clicked: ' + percentageClicked, percentageClicked],
                        ['Did not click: ' + percentageNotClicked, percentageNotClicked]
                    ];
                }

                console.log(percentageClicked, percentageNotClicked);
                var clickchart = {
                    chart: {
                        type: 'pie',
                    },

                    plotOptions: {
                        pie: {
                            size: '90%',
                            dataLabels: {
                                enabled: false
                            },
                            showInLegend: true,
                            point: {
                                events: {
                                    click: function () {
                                        console.log(this);
                                    }
                                }
                            }

                        }
                    },
                    colors: ['#F2D370', '#CCB25E'],
                    title: {
                        text: 'Click Rates'
                    },
                    series: [{
                        type: 'pie',
                        name: 'Number of Users',
                        data: clickedData,
                    }]
                };


                // var percentageRegistered = breakdown.opened.clicked.registered.rate;
                // var percentageNotRegistered = 1 - percentageRegistered;

                var percentageRegistered = breakdown.opened.clicked.registered.number;
                var percentageNotRegistered = breakdown.opened.clicked.number - percentageRegistered - breakdown.opened.clicked.purchased.number;
                var registeredData = [];

                if (percentageRegistered == 0 && percentageNotRegistered == 0) {
                    registeredData = [
                        ['Not Available', 0.00000001]
                    ]
                } else {
                    registeredData = [
                        ['Got Started: ' + percentageRegistered, percentageRegistered],
                        ['Did Not Get Started: ' + percentageNotRegistered, percentageNotRegistered]
                    ]
                }

                var registerchart = {
                    chart: {
                        type: 'pie',
                    },
                    colors: ['#AECEF2', '#495766'],
                    title: {
                        text: 'Get Started Rates'
                    },
                    plotOptions: {
                        pie: {
                            size: '90%',
                            dataLabels: {
                                enabled: false
                            },
                            showInLegend: true
                        }
                    },
                    series: [{
                        type: 'pie',
                        name: 'Number of Users',
                        data: registeredData
                    }]
                };

                // var percentagePurchased = breakdown.opened.clicked.purchased.rate;
                // var percentageNotPurchased = 1 - percentagePurchased;

                var percentagePurchased = breakdown.opened.clicked.purchased.number;
                var percentageNotPurchased = breakdown.opened.clicked.number - percentagePurchased;
                var purchasedData = [];

                if (percentagePurchased == 0 && percentageNotPurchased == 0) {
                    purchasedData = [
                        ['Not Available', 0.00000001]
                    ]
                } else {
                    purchasedData = [
                        ['Purchased: ' + percentagePurchased, percentagePurchased],
                        ['Did Not Purchase: ' + percentageNotPurchased, percentageNotPurchased]
                    ]
                }


                var purchasechart = {
                    chart: {
                        type: 'pie',
                    },
                    colors: ['#CCC7B4', '#66635A'],
                    title: {
                        text: 'Purchase Rates'
                    },
                    plotOptions: {
                        pie: {
                            size: '90%',
                            dataLabels: {
                                enabled: false
                            },
                            showInLegend: true
                        }
                    },
                    series: [{
                        type: 'pie',
                        name: 'Number of Users',
                        data: purchasedData
                    }]
                };


                this.setState({
                    campaignIndex: index,
                    campaign: campaign,
                    clickchart: clickchart,
                    openchart: openchart,
                    purchasechart: purchasechart,
                    registerchart: registerchart,
                    chartsload: false
                });


            }
        });


    },
    render: function () {
        {/*if (!this.props.campaigns) return (<div></div>);*/
        }
        var campaigns = this.props.campaigns.map(function (campaign, index) {

            if (!campaign.settings.title) {
                return;
            }
            return {
                text: campaign.settings.title + ' "' + campaign.settings.subject_line + '"',
                // id: campaign.campaign_id
                id: index
            };

        });
        var campaignDetailsHtml = '';
        if (this.state.campaign) {
            campaignDetailsHtml = (
                <div>
                    <h2 style={{color: '#587F6C'}}>{this.state.campaign.settings.title}</h2>
                    <h3 style={{color: '#CCB25E'}}>Subject Title: {this.state.campaign.settings.subject_line}</h3>
                    <h4 style={{color: '#66635A'}}>Emails Sent: {this.state.campaign.recipients.recipient_count}</h4>
                </div>
            )
        }

        var piechartsHtml = (
            <div>
                <div className="row">
                    <div className="col-xs-12" style={{textAlign: 'center'}}>
                        {campaignDetailsHtml}
                    </div>
                </div>
                <div className="row" style={{marginTop: '10px'}}>
                    <div className="col-xs-3" style={{padding: '0px'}}>
                        <ReactHighcharts config={this.state.openchart}></ReactHighcharts>
                    </div>
                    <div className="col-xs-3 col-xs-offset-0" style={{padding: '0px'}}>
                        <ReactHighcharts config={this.state.clickchart}></ReactHighcharts>
                    </div>
                    <div className="col-xs-3" style={{padding: '0px'}}>
                        <ReactHighcharts config={this.state.registerchart}></ReactHighcharts>
                    </div>
                    <div className="col-xs-3 col-xs-offset-0" style={{padding: '0px'}}>
                        <ReactHighcharts config={this.state.purchasechart}></ReactHighcharts>
                    </div>
                </div>
            </div>
        )
        if (this.state.chartsload) {
            piechartsHtml =
                <div style={{textAlign: 'center', marginTop: '100px'}}><i className="fa fa-spinner fa-spin fa-3x"/>
                </div>;
        } else if (this.state.campaign == null) {
            piechartsHtml = '';
        }

        return (
            <div className="container">
                <div className="row" style={{marginTop: '0px'}}>
                    <div className="col-xs-10 col-xs-offset-1 col-sm-6 col-sm-offset-3">
                        <h1 className="text-center">View Your Campaign Results</h1>
                    </div>
                </div>
                <br/>
                <div className="row">
                    <div className="col-xs-12">

                        <h3>Select A Campaign:</h3>
                        <Select2 style={{width: '30%'}}
                                 ref="campaign"
                                 value={this.state.campaignIndex}
                                 options={{placeholder: 'Select Campaign', allowClear: true}}
                                 data={campaigns}
                                 onSelect={this.changeList.bind(null, null)}
                        />

                    </div>
                </div>
                {piechartsHtml}
            </div>

        )
    }
});


module.exports = withRouter(MarketingPage);
