var React = require('react');
var createReactClass = require('create-react-class');
var withRouter = require('react-router-dom').withRouter;

var $ = require('jquery');
var DataTable = require('datatables.net-bs');
require('datatables.net-bs/css/dataTables.bootstrap.css');

var OrderModal = require('./OrderModal');


var CustomersList = createReactClass({
    getInitialState: function () {
        return {modalcustomer: null};
    },
    setModalCustomer: function (customer) {
        this.setState({modalcustomer: customer});
    },


    render: function () {
        var customersHtml = '';
        if (this.props.loading) {
            customersHtml =
                <div style={{textAlign:'center', marginTop:'100px'}}><i className="fa fa-spinner fa-spin fa-3x"/></div>
        } else {
            customersHtml = <CustomersTable customers={this.props.customers} setModalCustomer={this.setModalCustomer}/>;
        }


        return (
            <div>
                { this.props.loading ? '' :
                    <OrderModal customer={this.state.modalcustomer} action="add"/>
                }
                <div className="container-fluid">
                    <div className="row" style={{marginTop:'0px'}}>
                        <div className="col-xs-10 col-xs-offset-1 col-sm-6 col-sm-offset-3">
                            <h1 className="text-center">Our Customers</h1>
                        </div>
                    </div>
                    <div className="row" style={{marginTop:'30px'}}>
                        <div className="col-xs-12">
                            {customersHtml}

                        </div>
                    </div>
                </div>
            </div>
        );
    }
});


var CustomersTable = createReactClass({
        componentDidMount: function () {
            var table = $('#table').DataTable({
                "aaSorting": [],
                "aoColumnDefs": [
                    {"bSortable": false, "aTargets": [0,3, 4]},
                    {"bSearchable": false, "aTargets": [3,4]}
                ]

            });
        },
        toggleOrderModal: function (customer) {
            this.props.setModalCustomer(customer);
            $('#orderModal').modal('toggle');
        },
        focusCustomer: function (customer) {
            this.props.history.push(`/customers/${customer.customer_id}/orders`);
        }
        ,
        render: function () {
            var focusCustomer = this.focusCustomer;
            var toggleOrderModal = this.toggleOrderModal;
            var customers = this.props.customers.map(function (customer, index) {
            //console.log('what is the focus customer: ' + JSON.stringify(customer));
                return (
                    <tr key={customer.customer_id}>
                        <td className="col-xs-1" onClick={focusCustomer.bind(null, customer)}>{index + 1}</td>
                        <td className="col-xs-4" onClick={focusCustomer.bind(null, customer)}>{customer.customer_name}</td>
                        <td className="col-xs-5" onClick={focusCustomer.bind(null, customer)}>{customer.customer_email}</td>
                        <td className="col-xs-1">
                            <button className="btn btn-xs btn-primary" onClick={toggleOrderModal.bind(null,customer)}>Add
                                Order
                            </button>
                        </td>
                        <td className="col-xs-1">
                            <button className="btn btn-xs btn-primary" onClick={focusCustomer.bind(null, customer)}>View
                                Orders
                            </button>
                        </td>
                    </tr>
                )
            });
            return (
                <table id="table" className="table table-hover table-condensed">
                    <thead>
                    <tr>
                        <th>#</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Actions</th>
                        <th></th>
                    </tr>
                    </thead>
                    <tbody>
                    {customers}
                    </tbody>
                </table>
            );
        }
    })
    ;

CustomersTable = withRouter(CustomersTable);
module.exports = withRouter(CustomersList);
