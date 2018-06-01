var React = require('react');
var createReactClass = require('create-react-class');
var _ = require('lodash');
var $ = require('jquery');
var withRouter = require('react-router-dom').withRouter;
var Route = require('react-router-dom').Route;
var DataTable = require('datatables.net-bs');
require('datatables.net-bs/css/dataTables.bootstrap.css');

var CustomersList = require('./CustomersList');
var CustomerDetails = require('./CustomerDetails');


var CustomersPage = createReactClass({
    getInitialState: function () {
        return {customers: [], loading: true};
    },
    componentWillMount: function () {

        this.loadCustomers();
    },
    loadCustomers: function () {
        this.setState({loading: true});
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
            url: '/manager/api/getAllCustomers/',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            },
            method: 'GET',
            context: this,
            success: function (res) {
                this.setState({
                    customers: res.customers,
                    loading: false
                });
            }
        });


    },
    render: function () {
        const { loading, customers } = this.state;
        const match = this.props.match;
        return (
            <div>
                <Route path={`${match.url}/:customerId`} component={CustomerDetails} />
                <Route exact path={match.url} render={() =>
                    <CustomersList loading={loading} customers={customers} />}
                />
            </div>
        )
    }
});


module.exports = withRouter(CustomersPage);
