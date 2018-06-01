var React = require('react');
var createReactClass = require('create-react-class');
var _ = require('lodash');
var $ = require('jquery');
var ReactDOM = require('react-dom');
var Link = require('react-router-dom').Link;
var withRouter = require('react-router-dom').withRouter;
var swal = require('sweetalert');
var Multiselect = require('react-bootstrap-multiselect');
var DataTable = require('datatables.net-bs');
require('react-bootstrap-multiselect/css/bootstrap-multiselect.css');
require('sweetalert/dist/sweetalert.css');
require('datatables.net-bs/css/dataTables.bootstrap.css');

var OrderModal = require('./OrderModal');


var CustomerInfo = createReactClass({
    coffees: [],
    brew_methods: [],
    getInitialState: function () {


        return {modalorder: null, vouchers: [], packaging: 'DR', coffee:''};
    },
    componentDidMount: function () {
        // console.log('customer2',this.props.customer);
        var $this = this;
        this.getAvailableCoffees()
            .then(this.getBrewMethods())
            .then(this.updateForm($this.props.customer));


    },
    componentWillReceiveProps: function (nextprops) {
        if (this.coffees.length > 0 && this.brew_methods.length > 0) {
            this.updateForm(nextprops.customer);
        }
    },
    togglePrintStickerModal: function (orderid) {
            this.current_print_orderid = orderid;
            $('#printstickermodal').modal('toggle');

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

        return $.ajax({
            url: '/manager/api/getAvailableCoffees/',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            },
            context: this,
            success: function (res) {
                console.log('coffee loaded');
                this.coffees = res.coffees;
            }
        });

    },
    getBrewMethods: function () {
        var csrftoken = '';
        var cookies = document.cookie.split(';');
        _.map(cookies, function (cookie) {
            var keyValue = cookie.split('=');
            if (keyValue[0].trim() == 'csrftoken') {
                csrftoken = keyValue[1];
            }
            ;
        });

        return $.ajax({
            url: '/manager/api/brewMethods',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            },
            method: 'GET',
            dataType: 'json',
            context: this,
            success: function (res) {
                this.brew_methods = res;
            }
        });
    },
    updateForm: function (customer) {
        console.log('customer', customer);
        var $this = this;
        this.refs.firstname.value = customer.first_name;
        this.refs.lastname.value = customer.last_name;
        this.refs.email.value = customer.customer_email;
        this.refs.address1.value = customer.address_first;
        this.refs.address2.value = customer.address_second;
        this.refs.postalcode.value = customer.postal_code;
        this.refs.phone.value = customer.phone;
        this.refs.credits.value = customer.credits;
        this.refs.vouchers.value = customer.vouchers;

        this.refs.decaffeinated.checked = customer.decaffeinated;
        this.refs.different.checked = customer.different;
        this.refs.differentpods.checked = customer.different_pods;

        this.refs.cups.value = customer.cups;
        this.refs.intensity.value = customer.intense;
        this.refs.shippinginterval.value = customer.interval;
        this.refs.shippingintervalpods.value = customer.interval_pods;


        this.refs.packaging.value = customer.packaging_method;
        this.setState({packaging: customer.packaging_method,coffee: customer.coffee_id}, function () {
            $this.refs.brew_method.value = customer.brew_method;
        });
        this.initVouchers(customer);
        this.initFlavours(customer);


        // console.log(customer.vouchers);
        // console.log(this.refs.vouchers);

    },
    initVouchers: function (customer) {
        var csrftoken = '';
        var cookies = document.cookie.split(';');
        _.map(cookies, function (cookie) {
            var keyValue = cookie.split('=');
            if (keyValue[0].trim() == 'csrftoken') {
                csrftoken = keyValue[1];
            }
            ;
        });
        var $this = this;
        $.ajax({
            url: '/manager/api/getVouchers/',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            },
            method: 'GET',
            dataType: 'json',
            context: $this,
            success: function (res) {
                console.log(res);
                var vouchers = res.vouchers;
                var result = [];
                var customer_vouchers = customer.vouchers;

                _.map(customer_vouchers, function (voucher) {
                    result.push({value: voucher, selected: true});
                });

                var allVouchersCleaned = _.map(vouchers, function (voucher) {
                    return voucher.voucher_name;
                });

                var unselectedVouchers = _.difference(allVouchersCleaned, customer_vouchers);
                _.map(unselectedVouchers, function (voucher) {
                    result.push({value: voucher});
                })

                this.setState({vouchers: result});
            }
        });
    },
    initFlavours: function (customer) {
        var csrftoken = '';
        var cookies = document.cookie.split(';');
        _.map(cookies, function (cookie) {
            var keyValue = cookie.split('=');
            if (keyValue[0].trim() == 'csrftoken') {
                csrftoken = keyValue[1];
            }
            ;
        });
        var $this = this;
        $.ajax({
            url: '/manager/api/getFlavors/',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            },
            method: 'GET',
            dataType: 'json',
            context: $this,
            success: function (res) {
                console.log(res);
                var flavours = res.flavors;
                var result = [];
                var customer_flavours = customer.flavor;

                _.map(customer_flavours, function (flavour) {
                    result.push({value: flavour, selected: true});
                });

                var allFlavoursCleaned = _.map(flavours, function (flavour) {
                    return flavour.flavor_name;
                });
                var unselectedFlavours = _.difference(allFlavoursCleaned, customer_flavours);
                _.map(unselectedFlavours, function (flavour) {
                    result.push({value: flavour});
                })
                this.setState({flavours: result});
            }
        });
    },
    handleChangePackaging: function () {
        this.setState({packaging: this.refs.packaging.value});
    },
    handleSubmit: function (event) {
        event.preventDefault();

        var csrftoken = '';
        var cookies = document.cookie.split(';');
        _.map(cookies, function (cookie) {
            var keyValue = cookie.split('=');
            if (keyValue[0].trim() == 'csrftoken') {
                csrftoken = keyValue[1];
            }
            ;
        });

        var voucher_node = $(ReactDOM.findDOMNode(this.refs.vouchers));
        var flavour_node = $(ReactDOM.findDOMNode(this.refs.flavour));
        var selectedVouchers = $(voucher_node).val();
        var selectedFlavours = $(flavour_node).val();

        var data = {
            customer_id: this.props.customerId,
            first_name: this.refs.firstname.value,
            last_name: this.refs.lastname.value,
            customer_email: this.refs.email.value,
            address_first: this.refs.address1.value,
            address_second: this.refs.address2.value,
            postal_code: this.refs.postalcode.value,
            phone: this.refs.phone.value,
            credits: this.refs.credits.value,
            vouchers: selectedVouchers,
            coffee_id: this.refs.coffee.value,
            flavor: selectedFlavours,
            packaging_method: this.refs.packaging.value,
            brew_method: this.refs.brew_method.value,
            decaffeinated: this.refs.decaffeinated.checked,
            different: this.refs.different.checked,
            different_pods: this.refs.differentpods.checked,
            cups: this.refs.cups.value,
            intense: this.refs.intensity.value,
            interval: this.refs.shippinginterval.value,
            interval_pods: this.refs.shippingintervalpods.value,

        };

        console.log(data);
        // return;
        var $this = this;
        $.ajax({
            url: '/manager/api/editCustomerPreferences/',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            },
            method: 'POST',
            data: JSON.stringify(data),
            dataType: 'json',
            context: $this,
            success: function (res) {
                console.log(res);
                if (res.status == 200) {
                    swal({
                            title: "Success!",
                            text: "Customer preference has been edited successfully!",
                            type: "success",
                            confirmButtonColor: '#DAA62A'
                        });
                    // window.alert('Customer preference has been edited successfully!');
                    this.props.loadCustomerPreferences();
                } else {
                    // swal({
                    //         title: 'Error',
                    //         text: res.error_message,
                    //         type: 'warning',
                    //         confirmButtonColor: '#DAA62A'
                    //     });
                    window.alert(res.error_message);
                }

            },
        });
    },
    syncData: function () {
        console.log('sync data');
        this.refs.vouchers.syncData();
    },
    changeCoffee: function(){
      this.setState({coffee:this.refs.coffee.value});
    },
    render: function () {


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
        return (
            <div className="row">
                <div className="col-xs-12" style={{paddingLeft: '50px', paddingRight: '50px'}}>

                    <div className="row">
                        <div className="col-xs-12 col-md-12">
                            <h2>Personal Information</h2>
                            <form className="form-horizontal">
                                <div className="form-group">
                                    <label className="col-sm-3 control-label">First Name</label>
                                    <div className="col-sm-2">
                                        <input type="text" className="form-control" ref="firstname"/>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="col-sm-3 control-label">Last Name</label>
                                    <div className="col-sm-2">
                                        <input type="text" className="form-control" ref="lastname"/>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="col-sm-3 control-label">Email</label>
                                    <div className="col-sm-4">
                                        <input type="email" className="form-control" ref="email"/>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="col-sm-3 control-label">Address</label>
                                    <div className="col-sm-8">
                                        <input type="text" className="form-control" ref="address1"/>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="col-sm-3 control-label"></label>
                                    <div className="col-sm-8">
                                        <input type="text" className="form-control" ref="address2"/>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="col-sm-3 control-label">Postal Code</label>
                                    <div className="col-sm-8">
                                        <input type="text" className="form-control" ref="postalcode"/>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="col-sm-3 control-label">Phone</label>
                                    <div className="col-sm-2">
                                        <input className="form-control" ref="phone"/>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="col-sm-3 control-label">Credits</label>
                                    <div className="col-sm-2">
                                        <input className="form-control" ref="credits" placeholder="$ 0"/>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="col-sm-3 control-label">Vouchers</label>
                                    <div className="col-sm-3">
                                        <Multiselect multiple ref="vouchers" className="bs-multiselect"
                                                     data={this.state.vouchers}/>
                                    </div>
                                </div>
                            </form>
                        </div>
                        <div className="col-xs-12 col-md-12">
                            <h2>Preferences</h2>
                            <form className="form-horizontal">
                                <div className="form-group">
                                    <label className="col-sm-3 control-label">Coffee Type</label>
                                    <div className="col-sm-3">
                                        <select ref="coffee" className="form-control" id="select-coffee"
                                                onChange={this.changeCoffee} value={this.state.coffee}>
                                            {coffees}
                                        </select>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="col-sm-3 control-label">Flavour</label>
                                    <div className="col-sm-3">
                                        <Multiselect multiple ref="flavour" className="bs-multiselect"
                                                     data={this.state.flavours}/>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="col-sm-3 control-label">Packaging
                                        Method</label>
                                    <div className="col-sm-3">
                                        <select ref="packaging" className="form-control" id="select-packaging"
                                                onChange={this.handleChangePackaging}>
                                            <option value="DR">Drip Bags</option>
                                            <option value="WB">Whole Beans</option>
                                            <option value="GR">Ground</option>
                                            <option value="SP">Shot Pods</option>
                                        </select>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="col-sm-3 control-label">Brew Method</label>
                                    <div className="col-sm-3">
                                        <select ref="brew_method" className="form-control" id="select-packaging">
                                            {brew_methodsPrint}
                                        </select>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <div className="checkbox">
                                        <label
                                            className="col-sm-3 control-label"><b>Decaffeinated?</b></label>
                                        <div className="col-sm-3">
                                            <label className="checkbox-inline">
                                                <input type="checkbox" id="decaf" ref="decaffeinated"/>
                                            </label>
                                        </div>
                                    </div>
                                </div>

                                <div className="form-group">
                                    <div className="checkbox">
                                        <label
                                            className="col-sm-3 control-label"><b>Different?
                                        </b></label>
                                        <div className="col-sm-3">
                                            <label className="checkbox-inline">
                                                <input type="checkbox" ref="different" id="diff"/>
                                            </label>
                                        </div>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <div className="checkbox">
                                        <label className="col-sm-3 control-label"><b>Different
                                            Pods?</b></label>
                                        <div className="col-sm-3">
                                            <label className="checkbox-inline">
                                                <input type="checkbox" id="diffPods" ref="differentpods"/>
                                            </label>
                                        </div>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="col-sm-3 control-label">Cups Per Week</label>
                                    <div className="col-sm-1">
                                        <input type="number" className="form-control" id="cups" ref="cups"
                                               placeholder="7"/>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="col-sm-3 control-label">Intensity</label>
                                    <div className="col-sm-1">
                                        <input type="number" className="form-control" id="intensity" ref="intensity"
                                               placeholder="4"/>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="col-sm-3 control-label">Shipping
                                        Interval</label>
                                    <div className="col-sm-1">
                                        <input type="number" className="form-control" ref="shippinginterval"
                                               id="shipping_interval"
                                               placeholder="15"/>
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label className="col-sm-3 control-label">Shipping
                                        Interval
                                        (Pods)</label>
                                    <div className="col-sm-1">
                                        <input type="number" className="form-control" ref="shippingintervalpods"
                                               id="shipping_interval_pods"
                                               placeholder="7"/>
                                    </div>
                                </div>
                                <br/>
                                <div className="form-group">
                                    <div className="col-sm-offset-3 col-sm-8">
                                        <button className="btn btn-primary btn-default" onClick={this.handleSubmit}>
                                            Save Changes
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        )

    }
});


module.exports = withRouter(CustomerInfo);
