var React = require('react');
var createReactClass = require('create-react-class');
var _ = require('lodash');
var $ = require('jquery');
var ReactDOM = require('react-dom');
var Link = require('react-router-dom').Link;
var Route = require('react-router-dom').Route;
var withRouter = require('react-router-dom').withRouter;
var swal = require('sweetalert');
var moment = require('moment');
var DataTable = require('datatables.net-bs');
require('sweetalert/dist/sweetalert.css');
require('datatables.net-bs/css/dataTables.bootstrap.css');

var Utils = require('../utils');
var ApiRequest = Utils.ApiRequest;
var printPDF = Utils.printPDF;
var CustomerOrders = require('./CustomerOrders');
var CustomerInfo = require('./CustomerInfo');


var CustomerDetails = createReactClass({

    getInitialState: function () {
        return {orders: [], customer: {customer_name: '', customer_email: ''}};
    },
    componentWillMount: function () {

        this.loadCustomerOrders();
        this.loadCustomerPreferences();
    },
    loadCustomerPreferences: function () {
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
            customer_id: this.props.match.params.customerId,
        };
        $.ajax({
            url: '/manager/api/getCustomerPreferences/',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            },
            method: 'POST',
            data: JSON.stringify(data),
            dataType: 'json',
            context: this,
            success: function (res) {
                console.log('customerpref', res);
                this.setState({customer: res.customer_details});
            }
        });
    },


    loadCustomerOrders: function () {
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
            customer_id: this.props.match.params.customerId,
        };
        $.ajax({
            url: '/manager/api/customerOrders/',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            },
            method: 'POST',
            data: JSON.stringify(data),
            dataType: 'json',
            context: this,
            success: function (res) {
                console.log(res);
                this.setState({
                    orders: res.orders,
                });
            }
        });
    },
    printAddress: function () {
        const customer = this.props.match.params.customerId;
        ApiRequest.post('customerAddress', { customer }, { responseType: 'blob' })
          .then(resp => printPDF($('#pdfdoc'), resp))
          .catch(err => swal({ title: err, type: 'error' }));
    },
    //
    // componentDidUpdate: function () {
    //     window.scrollTo(0, 0);
    // },
    setTab: function (newTab) {
        // this.setState({activeTab: newTab});
        const customerId = this.props.match.params.customerId;
        this.props.history.push(`/customers/${customerId}/${newTab}`);
    },

    render: function () {
        var activeTab = this.props.history.location.pathname;
        activeTab = activeTab.substring(activeTab.lastIndexOf('/') + 1);
        const match = this.props.match;
        return (
            <div>
                <span id="pdfdoc"></span>
                <div className="row">
                    <div className="col-xs-12" style={{padding: '45px 50px 10px'}}>
                        <Link to="/customers"
                              style={{
                                  float: 'right',
                                  color: 'darkred',
                                  fontSize: '1.6em',
                                  margin: '-40px -10px',
                                  cursor: 'pointer'
                              }}
                              className="glyphicon glyphicon-remove"></Link>
                        <h1>{this.state.customer.customer_name}</h1>
                        <p style={{fontWeight: 'bold'}}>{this.state.customer.customer_email}{'\u00a0'}{'\u00a0'}
                            <button className="btn btn-default"
                                    onClick={this.printAddress}><i
                                className="fa fa-print"></i></button>
                        </p>
                    </div>
                </div>
                <div className="row">
                    <div className="col-xs-12" style={{paddingLeft: '50px'}}>
                        <ul className="nav nav-tabs">
                            <li className={activeTab == 'orders' ? 'active' : ''}
                                onClick={this.setTab.bind(null, 'orders')}><a>ORDERS</a></li>
                            <li className={activeTab == 'info' ? 'active' : ''}
                                onClick={this.setTab.bind(null, 'info')}><a>INFO</a></li>
                        </ul>
                    </div>
                </div>

                <Route path={`${match.url}/orders`} render={() =>
                    <CustomerOrders
                        customer={this.state.customer}
                        orders={this.state.orders}
                        loadCustomerOrders={this.loadCustomerOrders}
                    />}
                />
                <Route path={`${match.url}/info`} render={() =>
                    <CustomerInfo
                        customer={this.state.customer}
                        customerId={this.props.match.params.customerId}
                        loadCustomerPreferences={this.loadCustomerPreferences}
                    />}
                />
            </div>

        )
    }

});


module.exports = withRouter(CustomerDetails);
