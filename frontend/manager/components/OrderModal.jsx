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


var OrderModal = createReactClass({
    coffees: [],
    brew_methods: [],
    getInitialState: function () {
        return {price: 0.00};
    },
    componentWillMount: function () {
        this.getAvailableCoffees();
    },
    componentDidMount: function () {
        if (this.props.customer && this.props.action == 'add') {

            this.getCustomerPreferences();
        } else if (this.props.order && this.props.action == 'edit') {
            this.getCustomerOrder();
        }
    },
    dateFocus: function () {
        $('#shipping-date').focus();
    },
    componentWillReceiveProps: function (nextprops) {
        if ((nextprops.action == 'edit' && nextprops.order) || nextprops.action == 'add') {
            console.log('did compo receive props');
            if (nextprops.customer && nextprops.action == 'add') {
                this.getCustomerPreferences(nextprops);
            } else if (nextprops.order && nextprops.action == 'edit') {
                this.getCustomerOrder(nextprops);
            }
        }
    },
    getOrderPrice: function () {

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
            coffee_id: this.refs.coffee.value
        };
        var order = this.props.order;
        if (order) {
            data['order_id'] = order.order_id;
        }
        console.log(data);
        $.ajax({
            url: '/manager/api/getOrderPrice/',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            },
            method: 'POST',
            data: JSON.stringify(data),
            dataType: 'json',
            context: this,
            success: function (res) {
                console.log('orderprice', res);
                this.price = res.price;
                this.setState({price: res.price});
            }
        });

    },
    getAvailableCoffees: function () {

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
            url: '/manager/api/getAvailableCoffees/',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            },
            context: this,
            success: function (res) {
                this.coffees = res.coffees;
            }
        });

    },
    getCustomerPreferences: function (nextprops) {

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
            customer_id: nextprops.customer.customer_id
        };
        console.log('data', data);
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
                var defaultvalues = res.customer_details;
                this.refs.coffee.value = defaultvalues.coffee_id;
                this.refs.packaging.value = defaultvalues.packaging_method;

                if (defaultvalues.packaging_method != 'DR' && defaultvalues.packaging_method != 'SP') {
                    this.refs.brew_method.value = defaultvalues.brew_method;
                }
                this.refs.shipping_date.value = moment(defaultvalues.shipping_date * 1000).format('MMMM DD, YYYY');

                $('input[name="daterange"]').daterangepicker({
                    singleDatePicker: true,
                    startDate: moment(defaultvalues.shipping_date * 1000),
                    locale: {
                        format: 'DD-MM-YYYY'
                    }
                });
                this.getOrderPrice();
                this.handleChangePackaging();


            }
        });

    },

    getCustomerOrder: function (nextprops) {

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
            order_id: nextprops.order.order_id
        };
        $.ajax({
            url: '/manager/api/getOrderDetails/',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            },
            method: 'POST',
            data: JSON.stringify(data),
            dataType: 'json',
            context: this,
            success: function (res) {
                console.log(res);
                var defaultvalues = res.order_details;
                this.refs.coffee.value = defaultvalues.coffee_id;
                if (defaultvalues.packaging_method != 'DR' && defaultvalues.packaging_method != 'SP') {
                    this.refs.brew_method.value = defaultvalues.brew_method;
                }
                this.refs.packaging.value = defaultvalues.packaging_method;
                this.refs.shipping_date.value = moment(defaultvalues.shipping_date * 1000).format('MMMM DD, YYYY');

                $('input[name="daterange"]').daterangepicker({
                    singleDatePicker: true,
                    startDate: moment(defaultvalues.shipping_date * 1000),
                    locale: {
                        format: 'DD-MM-YYYY'
                    }
                });
                this.setState({customPrice: defaultvalues.custom_price});

                this.getOrderPrice();
                this.handleChangePackaging();

            }
        });

    },

    submit: function (e) {
        e.preventDefault();

        var coffee_id = this.refs.coffee.value;
        var brew_method = this.refs.brew_method.value;
        var packaging = this.refs.packaging.value;
        var shipping_date = this.refs.shipping_date.value;
        var recurrent = this.refs.recurrent ? this.refs.recurrent.checked : '';

        var customPrice = this.refs.customPrice ? this.refs.customPrice.checked : '';

        var csrftoken = '';
        var cookies = document.cookie.split(';');
        _.map(cookies, function (cookie) {
            var keyValue = cookie.split('=');
            if (keyValue[0].trim() == 'csrftoken') {
                csrftoken = keyValue[1];
            }
            ;
        });

        var data;
        if (this.props.action == 'add') {
            data = {
                customer_id: this.props.customer.customer_id,
                coffee_id: coffee_id,
                brew_method: brew_method,
                packaging_method: packaging,
                shipping_date: shipping_date,
                recurrent: recurrent
            };
        } else if (this.props.action == 'edit') {
            data = {
                order_id: this.props.order.order_id,
                coffee_id: coffee_id,
                brew_method: brew_method,
                packaging_method: packaging,
                shipping_date: shipping_date,
                custom_price: customPrice
            };

            if (customPrice){
                data.price = parseFloat(this.state.price);
            } else {
            }

        }

        console.log('data', data)

        var url = '/manager/api/addOrder/';
        if (this.props.action == 'edit') {
            url = '/manager/api/editOrder/';
        }
        $.ajax({
            url: url,
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            },
            method: 'POST',
            data: JSON.stringify(data),
            dataType: 'json',
            context: this,
            success: function (res) {
                console.log(res);
                if (res.status == 200) {
                    if (this.props.action == 'edit') {
                        this.props.callback();
                    }
                    $('#orderModal').modal('toggle');
                } else {
                    // window.alert(res.error_message);
                    swal({
                        title: 'Warning',
                        text: res.error_message,
                        type: 'warning',
                        confirmButtonColor: '#F55449'
                    });
                }
            }
        });
    },
    handleChangePackaging: function () {
        this.setState({packaging: this.refs.packaging.value});
    },
    customPriceCheckboxHandler: function () {
        var customPrice = this.refs.customPrice.checked;
        if (customPrice) {
            this.setState({customPrice: this.refs.customPrice.checked});
        } else {
            this.setState({customPrice: this.refs.customPrice.checked, price: this.price});
        }
    },
    priceChange: function () {
        var newVal = this.refs.price.value;

        if (isNaN(newVal) || newVal < 0) {
            return;
        }
        this.setState({price: this.refs.price.value});
    },
    render: function () {

        console.log('CUSTOMPRICE??', this.state.customPrice);
        if (this.props.customer) {
            var customername = this.props.customer.customer_name;
        }

        var coffees = this.coffees.map(function (coffee) {
            return (
                <option key={coffee.coffee_id} value={coffee.coffee_id}>{coffee.coffee_name}</option>
            )
        });
        var brew_methods = [];
        if (this.state.packaging == 'DR') {
            brew_methods = ['Drip'];
        } else if (this.state.packaging == 'SP') {
            brew_methods = ['Nespresso'];
        } else if (this.state.packaging == 'WB' || this.state.packaging == 'GR') {
            brew_methods = ['Aeropress', 'Drip', 'Espresso', 'French press', 'Stove top', 'None'];
        }
        // console.log('filter', filter);

        brew_methodsPrint = brew_methods.map(function (brew_method) {
            return (
                <option key={brew_method} value={brew_method}>{brew_method}</option>
            )
        });
        console.log(this.state.customPrice);


        return (
            <div className="modal fade" id="orderModal" tabIndex="-1" role="dialog" aria-labelledby="myModalLabel"
                 aria-hidden="true">
                <div className="modal-dialog">
                    <div className="modal-content">
                        <div className="modal-header">
                            <button type="button" className="close" data-dismiss="modal" aria-label="Close"><span
                                aria-hidden="true">&times;</span></button>
                            <h3 className="modal-title">Order Form for {customername}</h3>
                        </div>
                        <div className="modal-body">
                            <form onSubmit={this.submit}>

                                <fieldset className="form-group">
                                    <label>Select a Coffee</label>
                                    <select ref="coffee" className="form-control" id="select-coffee"
                                            onChange={this.getOrderPrice}>
                                        {coffees}
                                    </select>
                                </fieldset>

                                <fieldset className="form-group">
                                    <label>Select a Packaging Method</label>
                                    <select ref="packaging" className="form-control" id="select-packaging"
                                            onChange={this.handleChangePackaging}>
                                        <option value="DR">Drip Bags</option>
                                        <option value="WB">Whole Beans</option>
                                        <option value="GR">Ground</option>
                                        <option value="SP">Shot Pods</option>
                                    </select>
                                </fieldset>

                                <fieldset className="form-group">
                                    <label>Select a Brewing Method</label>
                                    <select ref="brew_method" className="form-control" id="select-packaging">
                                        {brew_methodsPrint}
                                    </select>
                                </fieldset>

                                <fieldset className="form-group">
                                    <label>Shipping Date</label>
                                    <div className="input-group">
                                        <input className="form-control input" name="daterange" id="shipping-date"
                                               ref="shipping_date"
                                               placeholder="Choose shipping date" required/>
                                        <div name="daterange" onClick={this.dateFocus} className="input-group-addon"><i
                                            className="fa fa-calendar pull-right"></i></div>
                                    </div>
                                </fieldset>

                                { this.props.action == 'add' ?
                                    <fieldset>
                                        <input type="checkbox" ref="recurrent"/> <label> Recurring?</label>
                                    </fieldset>
                                    :
                                    <fieldset>
                                        <input type="checkbox" ref="customPrice" checked={this.state.customPrice}
                                               onChange={this.customPriceCheckboxHandler}/> <label> Custom
                                        Price?</label>
                                    </fieldset>
                                }


                                { this.props.action == 'add' || !this.state.customPrice ?
                                    <div style={{fontWeight: 'bold', fontSize: '1.1em', textAlign: 'center'}}>
                                        Total Price: ${this.state.price} </div>
                                    :
                                    <div style={{fontWeight: 'bold', fontSize: '1.1em', textAlign: 'center'}}>
                                        Total Price: $<input value={this.state.price} onChange={this.priceChange}
                                                             ref="price" style={{width: '70px'}}/></div>
                                }
                                <div style={{textAlign: 'center'}}>
                                    <button type="submit"
                                            style={{
                                                paddingLeft: '30px',
                                                paddingRight: '30px',
                                                marginTop: '10px',
                                                width: '100%'
                                            }}
                                            className="btn btn-primary">Submit
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
});


module.exports = withRouter(OrderModal);
