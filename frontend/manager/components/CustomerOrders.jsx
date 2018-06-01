var React = require('react');
var createReactClass = require('create-react-class');
var _ = require('lodash');
var $ = require('jquery');
var ReactDOM = require('react-dom');
var Link = require('react-router-dom').Link;
var withRouter = require('react-router-dom').withRouter;
var swal = require('sweetalert');
var DataTable = require('datatables.net-bs');
var moment = require('moment');
require('sweetalert/dist/sweetalert.css');
require('datatables.net-bs/css/dataTables.bootstrap.css');

var OrderModal = require('./OrderModal');
var Utils = require('../utils');


var CustomerOrders = createReactClass({
    getInitialState: function () {
        return {modalorder: false};
    },

    toggleOrderModal: function (order) {
        this.setState({modalorder: order});
        $('#orderModal').modal('toggle');
    },

    resendOrder: function (order) {
        console.log(order);

        // var confirm = window.confirm('Resend this order?');
        // if (!confirm) {
        //     return;
        // }
        var $this = this;
        var resendHandler = function () {
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
                order_id: order.order_id
            };
            $.ajax({
                url: '/manager/api/resendOrder/',
                beforeSend: function (xhr) {
                    xhr.setRequestHeader('X-CSRFToken', csrftoken);
                },
                method: 'POST',
                data: JSON.stringify(data),
                dataType: 'json',
                context: $this,
                success: function (res) {
                    console.log(res);
                    this.props.loadCustomerOrders();
                    // window.alert(res.message);
                    swal({
                        title: "Done!",
                        text: res.message,
                        type: "success",
                        confirmButtonColor: '#DAA62A'
                    });
                }
            });
        }
        swal({
                title: "Confirm!",
                text: "Resend this order?",
                type: "warning",
                showCancelButton: true,
                confirmButtonColor: "#DD6B55",
                confirmButtonText: "Yes, resend this order!",
                closeOnConfirm: false
            },
            function (confirm) {
                if (confirm) {
                    resendHandler();
                }
            }
        );

    },

    cancelOrder: function (order) {


        // var confirm = window.confirm('Are you sure you want to cancel this order?');
        //
        // if (!confirm) {
        //     return;
        // }
        var $this = this;
        var cancelHandler = function () {
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
                order_id: order.order_id
            };
            $.ajax({
                url: '/manager/api/cancelOrder/',
                beforeSend: function (xhr) {
                    xhr.setRequestHeader('X-CSRFToken', csrftoken);
                },
                method: 'POST',
                data: JSON.stringify(data),
                dataType: 'json',
                context: $this,
                success: function (res) {
                    console.log(res);
                    this.props.loadCustomerOrders();
                    // window.alert(res.message);
                    swal({
                        title: "Done!",
                        text: res.message,
                        type: "success",
                        confirmButtonColor: '#DAA62A'
                    });
                }
            });

        }
        swal({
                title: "Confirm",
                text: "Are you sure you want to cancel this order?",
                type: "warning",
                showCancelButton: true,
                confirmButtonColor: "#DD6B55",
                confirmButtonText: "Yes, cancel this order!",
                closeOnConfirm: false
            },
            function (confirm) {
                if (confirm) {
                    cancelHandler();
                }
            }
        );

    },


    render: function () {
        var toggleOrderModal = this.toggleOrderModal;
        var resendOrder = this.resendOrder;
        var cancelOrder = this.cancelOrder;
        var orders = this.props.orders.map(function (order) {
            order['statusPrint'] = Utils.formatStatus(order.status);
            order['packagingPrint'] = Utils.formatPackaging(order.packaging_method);
            return (
                <tr key={order.order_id}>
                    <td>{order.order_id}</td>
                    <td>{order.coffee}</td>
                    <td>{order.brew_method}</td>
                    <td>{order.packagingPrint}</td>
                    <td>{moment(order.created_date * 1000).format('MMMM DD,YYYY hh:mmA')}</td>
                    <td>{moment(order.shipping_date * 1000).format('MMMM DD,YYYY hh:mmA')}</td>
                    <td>{order.statusPrint}</td>
                    <td style={{minWidth:'160px'}}>
                        <div className="row">
                            <button className="btn btn-primary btn-xs" onClick={toggleOrderModal.bind(null, order)}>Edit
                            </button>

                            <button className="btn btn-danger btn-xs" style={{margin: '0 10px'}}
                                    onClick={cancelOrder.bind(null, order)} disabled={order.status != 'AC'}>Cancel
                            </button>
                            <button className="btn btn-info btn-xs" disabled={order.status != 'SH'}
                                    onClick={resendOrder.bind(null, order)}>Resend
                            </button>
                        </div>
                    </td>
                </tr>
            )
        });

        if (this.props.customer) {
            return (
                <div>
                    <OrderModal order={this.state.modalorder} customer={this.props.customer} action="edit"
                                callback={this.props.loadCustomerOrders}/>

                    <div className="row">
                        <div className="col-xs-12" style={{padding: '0px 50px 50px'}}>
                            <table className="table">
                                <thead>
                                <tr>
                                    <th>Order ID</th>
                                    <th>Coffee</th>
                                    <th>Brew Method</th>
                                    <th>Packaging</th>
                                    <th>Created</th>
                                    <th>Shipping Date</th>
                                    <th>Status</th>
                                    <th>Action</th>
                                </tr>
                                </thead>
                                <tbody>
                                {this.props.orders.length > 0 ? orders : ''}
                                </tbody>
                                <tfoot></tfoot>
                            </table>
                            {this.props.orders.length == 0 ? (
                                (
                                    <div style={{width: '100%'}}>
                                        <h3 style={{textAlign: 'center', marginTop: '50px', fontStyle: 'italic'}}>
                                            -{'\u00a0'}
                                            No {'\u00a0'} orders {'\u00a0'}-</h3>
                                    </div>
                                )
                            ) : ''}
                        </div>
                    </div>
                </div>

            )
        } else {
            return <div></div>
        }

    }
});


module.exports = withRouter(CustomerOrders);
