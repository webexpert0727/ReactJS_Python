var React = require('react');
var createReactClass = require('create-react-class');
var _ = require('lodash');
var $ = require('jquery');
var withRouter = require('react-router-dom').withRouter;
var ReactCSSTransitionGroup = require('react-addons-css-transition-group');
const ReactHighcharts = require('react-highcharts');
var Utils = require('../utils');
var moment = require('moment');
var DataTable = require('datatables.net-bs');


var swal = require('sweetalert');
require('sweetalert/dist/sweetalert.css');
require('datatables.net-bs/css/dataTables.bootstrap.css');


var InventoryPage = createReactClass({
        loadCount: 3,
        threshold: 20,
        dates: [moment().add(-1, 'WEEK').startOf('week'), moment().startOf('week'), moment(), moment().add(1, 'WEEK').startOf('week')],
        getInitialState: function () {
            return {loadCount: 0, updated: 0, threshold: 0};
        },

        componentWillMount: function () {
            this.getActiveBeans();
            this.getInactiveBeans();
            this.getThreshold();

        },

        getActiveBeans: function () {
            var csrftoken = '';
            var cookies = document.cookie.split(';');
            _.map(cookies, function (cookie) {
                var keyValue = cookie.split('=');
                if (keyValue[0].trim() == 'csrftoken') {
                    csrftoken = keyValue[1];
                }
                ;
            });

            var dates = JSON.stringify([this.dates[0].format('DD-MM-YYYY'), this.dates[1].format('DD-MM-YYYY'), this.dates[2].format('DD-MM-YYYY')]);

            $.ajax({
                url: '/manager/api/getActiveBeans?dates=' + dates,
                beforeSend: function (xhr) {
                    xhr.setRequestHeader('X-CSRFToken', csrftoken);
                },
                method: 'GET',
                dataType: 'json',
                context: this,
                success: function (res) {
                    console.log(res);

                    var sorted_beans = _.sortBy(res.beans, function (bean) {
                        return bean.bean_name;
                    });

                    var series = [];
                    var threshold_data = [];
                    var $this = this;

                    _.map(sorted_beans, function (bean) {
                        var data = [];
                        _.map(bean.weeks, function (week) {
                            data.push(week.stock);
                        });
                        var currStock = bean.weeks[2].stock;
                        var roast = bean.estimated_amount_to_roast;
                        var nextWeek = Math.max(currStock - roast, 0);
                        data.push(nextWeek);
                        // threshold_data.push($this.threshold);

                        series.push({
                            name: bean.bean_name,
                            data: data
                        });
                    });
                    // series.push({
                    //     name: 'THRESHOLD',
                    //     data: threshold_data
                    // })


                    var chart = {
                        title: {
                            text: null,
                            x: -20 //center
                        },
                        subtitle: {
                            text: null,
                            x: -20
                        },
                        chart: {
                            marginBottom: 70 + sorted_beans.length * 12 //increase based on number of beans
                        },
                        xAxis: {
                            // categories: [this.dates[0].format('DD/MM'), this.dates[1].format('DD/MM'), this.dates[2].format('DD/MM'), this.dates[3].format('DD/MM')]
                            categories: [this.dates[0].format('DD/MM'), this.dates[1].format('DD/MM'), this.dates[2].format('DD/MM'), 'Next Week']
                        },
                        yAxis: {
                            title: {
                                text: 'Stock Level (kg)'
                            },
                            plotLines: [{
                                value: 0,
                                width: 1,
                                color: '#808080'
                            }]
                        },
                        tooltip: {
                            valueSuffix: 'KG'
                        },
                        legend: {
                            align: 'center',
                            floating: true,
                            verticalAlign: 'bottom',
                            borderWidth: 0,
                            layout: 'vertical',
                        },
                        series: series
                    };


                    this.setState({beans: sorted_beans, loadCount: this.state.loadCount + 1, stockchart: chart});
                }
            });
        },
        getInactiveBeans: function () {
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
                url: '/manager/api/getInactiveBeans',
                beforeSend: function (xhr) {
                    xhr.setRequestHeader('X-CSRFToken', csrftoken);
                },
                method: 'GET',
                dataType: 'json',
                context: this,
                success: function (res) {
                    console.log(res);
                    this.setState({inactivebeans: res.inactive_beans, loadCount: this.state.loadCount + 1});
                }
            });
        },

        getThreshold: function () {
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
                url: '/manager/api/getThreshold',
                beforeSend: function (xhr) {
                    xhr.setRequestHeader('X-CSRFToken', csrftoken);
                },
                method: 'GET',
                dataType: 'json',
                context: this,
                success: function (res) {
                    console.log(res);

                    if (res.status == 200) {
                        this.setState({loadCount: this.state.loadCount + 1, threshold: res.threshold});
                    } else {
                        this.setState({loadCount: this.state.loadCount + 1});

                    }
                }
            });
        },
        changeThreshold: function (event) {
            var newThreshold = event.target.value;

            this.setState({threshold: newThreshold});
        },
        updateThreshold: function () {
            var csrftoken = '';
            var cookies = document.cookie.split(';');
            _.map(cookies, function (cookie) {
                var keyValue = cookie.split('=');
                if (keyValue[0].trim() == 'csrftoken') {
                    csrftoken = keyValue[1];
                }
                ;
            });

            var threshold = this.refs.threshold.value;

            var data = {
                threshold: threshold
            }

            $.ajax({
                url: '/manager/api/updateThreshold',
                beforeSend: function (xhr) {
                    xhr.setRequestHeader('X-CSRFToken', csrftoken);
                },
                method: 'POST',
                data: JSON.stringify(data),
                dataType: 'json',
                context: this,
                success: function (res) {
                    console.log(res);

                    this.setState({threshold: threshold});

                    if (res.status == 200) {
                        swal({
                            title: "Success!",
                            text: res.message,
                            type: "success",
                            confirmButtonColor: '#DAA62A'
                        });
                    } else {
                        swal({
                            title: 'Error',
                            text: res.error_message,
                            type: 'warning',
                            confirmButtonColor: '#DAA62A'
                        });
                        // window.alert(res.error_message);
                    }
                }
            });
        },
        deactivateBean: function (bean, stock) {
            console.log(status);
            console.log(bean);

            var csrftoken = '';
            var cookies = document.cookie.split(';');
            _.map(cookies, function (cookie) {
                var keyValue = cookie.split('=');
                if (keyValue[0].trim() == 'csrftoken') {
                    csrftoken = keyValue[1];
                }
                ;
            });

            var data = [{
                bean_id: bean.bean_id,
                status: false,
                stock: 0
            }];


            var ajax = $.ajax({
                url: '/manager/api/updateBean',
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
                        this.getActiveBeans();
                        this.getInactiveBeans();
                        swal({
                            title: "Success!",
                            text: bean.bean_name + ' has been deactivated!',
                            type: "success",
                            confirmButtonColor: '#DAA62A'
                        });
                        // window.alert(bean.bean_name + ' has been deactivated!');

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
        activateBean: function (bean) {
            console.log(status);
            console.log(bean);

            var csrftoken = '';
            var cookies = document.cookie.split(';');
            _.map(cookies, function (cookie) {
                var keyValue = cookie.split('=');
                if (keyValue[0].trim() == 'csrftoken') {
                    csrftoken = keyValue[1];
                }
                ;
            });

            var data = [{
                bean_id: bean.bean_id,
                status: true,
                stock: 0
            }];


            var ajax = $.ajax({
                url: '/manager/api/updateBean',
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
                        this.getActiveBeans();
                        this.getInactiveBeans();
                        swal({
                            title: "Success!",
                            text: bean.bean_name + ' has been activated!',
                            type: "success",
                            confirmButtonColor: '#DAA62A'
                        });
                        // window.alert(bean.bean_name + ' has been activated!');

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
        toggleNewBeanModal: function () {
            $('#newBeanModal').modal('toggle');
        },
        submitNewBean: function (e) {
            var beanname = this.refs.beanname.value;
            var initialstock = this.refs.initialstock.value;

            console.log(beanname, initialstock);
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

            var data = {
                name: beanname,
                stock: initialstock,
            };


            var ajax = $.ajax({
                url: '/manager/api/addNewBean',
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
                        $('#newBeanModal').modal('toggle');
                        this.refs.beanname.value = '';
                        this.refs.initialstock.value = '';
                        this.getActiveBeans();
                        swal({
                            title: "Success!",
                            text: initialstock + 'kg of ' + beanname + ' added!',
                            type: "success",
                            confirmButtonColor: '#DAA62A'
                        });
                        // window.alert(initialstock + 'kg of ' + beanname + ' added!');

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
        updateAllStocks: function () {
            this.setState({updated: 0});
            var $this = this;

            var beans = [];

            _.map(this.state.beans, function (bean) {
                var oldStockVal = bean.weeks[2].stock;
                var newStockVal = $this.refs[bean.bean_id].value;
                if (newStockVal >= 0 && oldStockVal != newStockVal) {
                    beans.push({
                        bean_id: bean.bean_id,
                        status: true,
                        stock: parseInt(newStockVal)
                    })
                }
            });

            var csrftoken = '';
            var cookies = document.cookie.split(';');
            _.map(cookies, function (cookie) {
                var keyValue = cookie.split('=');
                if (keyValue[0].trim() == 'csrftoken') {
                    csrftoken = keyValue[1];
                }
                ;
            });

            var data = beans;
            console.log(data);

            var ajax = $.ajax({
                url: '/manager/api/updateBean',
                beforeSend: function (xhr) {
                    xhr.setRequestHeader('X-CSRFToken', csrftoken);
                },
                method: 'POST',
                data: JSON.stringify(data),
                dataType: 'json',
                jsonp: false,
                context: $this,
                success: function (res) {
                    console.log(res);
                    if (res.status == 200) {
                        $this.getActiveBeans();
                        $this.getInactiveBeans();
                        $this.getThreshold();

                    } else {
                        swal({
                            title: 'Error',
                            text: res.error_message,
                            type: 'warning',
                            confirmButtonColor: '#DAA62A'
                        });
                        // window.alert(res.error_message);
                    }
                    $this.setState({loadCount: 0, updated: $this.state.updated + 1});

                },
                error: function (e) {
                    console.log(e);
                }
            });

        },
        render: function () {
            console.log('stockchart', this.state.stockchart);
            if (this.state.loadCount < this.loadCount) {
                return (
                    <div className="container">
                        <div className="row" style={{marginTop: '0px', marginBottom: '20px'}}>
                            <div className="col-xs-10 col-xs-offset-1 col-sm-6 col-sm-offset-3">
                                <h1 className="text-center">Coffee Beans Inventory</h1>
                            </div>
                        </div>
                        <div style={{textAlign: 'center', marginTop: '130px'}}><i className="fa fa-spinner fa-spin fa-3x"/>
                        </div>
                    </div>
                )
            }
            var $this = this;

            var activeTableHtml = null;
            if (this.state.beans) {
                activeTableHtml = this.state.beans.map(function (bean) {
                    var weeks = bean.weeks;

                    var currStock = bean.weeks[2].stock;
                    var roast = bean.estimated_amount_to_roast;
                    var nextWeek = Math.max(currStock - roast, 0);
                    var status = Utils.getBeanStatus(nextWeek, $this.state.threshold);
                    return (
                        <tr key={bean.bean_id}>
                            <td><i className="fa fa-circle" style={{color: status}}></i></td>
                            <td>{bean.bean_name}</td>
                            <td>{weeks[0].stock}</td>
                            <td>{weeks[1].stock}</td>
                            <td><input className="form-control input-sm" ref={bean.bean_id} type="number" min="0" required
                                       defaultValue={weeks[2].stock}/></td>
                            <td style={{fontStyle: 'italic'}}>{nextWeek}</td>
                            <td style={{fontStyle: 'italic'}}>{bean.estimated_amount_to_roast}</td>
                            {/*<td style={{fontStyle: 'italic'}}>{bean.estimated_date_to_roast}</td>*/}
                            <td>
                                <button className="btn btn-primary btn-sm"
                                        onClick={$this.deactivateBean.bind(null, bean, weeks[2].stock)}>
                                    deactivate
                                </button>
                            </td>
                        </tr>)
                });
            }

            var inactiveTableHtml = null;
            if (this.state.inactivebeans) {

                inactiveTableHtml = this.state.inactivebeans.map(function (bean) {
                    return (
                        <tr key={bean.bean_id}>
                            <td>{bean.bean_name}</td>
                            <td>{moment(bean.created_date * 1000).format('DD-MM-YYYY')}</td>
                            <td>{moment(bean.last_active_date * 1000).format('DD-MM-YYYY')}</td>
                            <td>{bean.total_roasted}</td>
                            <td>
                                <button className="btn btn-success btn-sm" onClick={$this.activateBean.bind(null, bean)}>
                                    activate
                                </button>
                            </td>
                        </tr>
                    )

                });

            }


            return (
                <div className="container-fluid">

                    <div className="modal fade" id="newBeanModal" tabIndex="-1" role="dialog" aria-labelledby="myModalLabel"
                         aria-hidden="true">
                        <div className="modal-dialog">
                            <div className="modal-content">
                                <div className="modal-header">
                                    <button type="button" className="close" data-dismiss="modal" aria-label="Close"><span
                                        aria-hidden="true">&times;</span></button>
                                    <h3 className="modal-title">Add New Bean</h3>
                                </div>
                                <div className="modal-body">
                                    <form onSubmit={this.submitNewBean}>


                                        <fieldset className="form-group">
                                            <label>Bean name</label>
                                            <input className="form-control" ref="beanname" placeholder="" required/>
                                        </fieldset>
                                        <fieldset className="form-group">
                                            <label>Initial stock level (kg)</label>
                                            <input className="form-control" type="number" ref="initialstock" placeholder=""
                                                   required min="0"/>
                                        </fieldset>


                                        <button type="submit"
                                                style={{
                                                    paddingLeft: '30px',
                                                    paddingRight: '30px',
                                                    marginTop: '10px',
                                                    width: '100%'
                                                }}
                                                className="btn btn-success">Submit
                                        </button>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>


                    <div className="row" style={{marginTop: '0px'}}>
                        <div className="col-xs-10 col-xs-offset-1 col-sm-6 col-sm-offset-3">
                            <h1 className="text-center">Coffee Beans Inventory</h1>
                        </div>
                    </div>
                    <div className="row">
                        <div className="col-xs-7">
                            <div className="row">
                                <div className="col-xs-12">
                                    <div className="row">
                                        <div className="col-xs-3">
                                            <h2>Active Beans</h2>
                                        </div>
                                        <div className="col-xs-9" style={{paddingTop: '28px'}}>
                                            { activeTableHtml ?
                                                <div>
                                                    <div className="col-xs-6" style={{textAlign: 'center'}}>
                                                        <button className="btn btn-primary" onClick={this.updateAllStocks}
                                                                style={{width: '100%'}}>Update Stock
                                                            Levels
                                                        </button>
                                                    </div>
                                                    < div className="col-xs-6" style={{textAlign: 'center'}}>
                                                        <button className="btn btn-success"
                                                                onClick={this.toggleNewBeanModal}
                                                                style={{width: '100%'}}>Add new coffeebean
                                                        </button>
                                                    </div>
                                                </div>
                                                :
                                                <div className="col-xs-12" style={{textAlign: 'center'}}>
                                                    <button className="btn btn-success" onClick={this.toggleNewBeanModal}
                                                            style={{width: '100%'}}>Add new coffeebean
                                                    </button>
                                                </div>
                                            }
                                        </div>
                                    </div>
                                    <div className="row">
                                        <div className="col-xs-12">
                                            { activeTableHtml ?
                                                (<table className="table table-hover">
                                                        <thead>
                                                        <tr>
                                                            <th style={{width: '5%'}}>Status</th>
                                                            <th style={{width: '15%'}}>Coffee</th>

                                                            <th style={{width: '10%'}}>{this.dates[0].format('DD/MM')}
                                                            </th>
                                                            <th style={{width: '10%'}}>{this.dates[1].format('DD/MM')}
                                                            </th>
                                                            <th style={{width: '30%'}}>Today
                                                            </th>
                                                            <th style={{width: '15%', fontStyle: 'italic'}}>Next week</th>
                                                            <th style={{width: '15%', fontStyle: 'italic'}}>Roast Amt</th>
                                                            {/*<th style={{width: '20%', fontStyle: 'italic'}}>Est. Roast*/}
                                                                {/*Date*/}
                                                            {/*</th>*/}
                                                            <th></th>
                                                        </tr>
                                                        </thead>
                                                        <tbody>
                                                        {activeTableHtml}
                                                        </tbody>
                                                    </table>
                                                ) :
                                                (
                                                    <h3 style={{
                                                        textAlign: 'center',
                                                        marginTop: '20px',
                                                        marginBottom: '40px',
                                                        fontStyle: 'italic'
                                                    }}>
                                                        -{'\u00a0'}
                                                        No {'\u00a0'} active {'\u00a0'} beans {'\u00a0'}-</h3>
                                                )
                                            }
                                        </div>
                                    </div>

                                </div>
                            </div>

                            <div className="row">
                                <div className="col-xs-12">
                                    <div className="row">
                                        <div className="col-xs-12">
                                            <hr/>
                                            <h2>Inactive Beans</h2>
                                        </div>
                                    </div>
                                    <div className="row">
                                        <div className="col-xs-12">
                                            { inactiveTableHtml ?
                                                <table className="table table-hover">
                                                    <thead>
                                                    <tr>
                                                        <th style={{width: '20%'}}>Coffee</th>
                                                        <th style={{width: '20%'}}>Date Created</th>
                                                        <th style={{width: '20%'}}>Last Active</th>
                                                        <th style={{width: '30%'}}>Total Roasted (kg)</th>
                                                        <th style={{width: '10%'}}></th>
                                                    </tr>
                                                    </thead>
                                                    <tbody>
                                                    {inactiveTableHtml}
                                                    </tbody>
                                                </table>
                                                :
                                                (
                                                    <h3 style={{
                                                        textAlign: 'center',
                                                        marginTop: '20px',
                                                        marginBottom: '40px',
                                                        fontStyle: 'italic'
                                                    }}>
                                                        -{'\u00a0'}
                                                        No {'\u00a0'} inactive {'\u00a0'} beans {'\u00a0'}-</h3>
                                                )
                                            }
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="col-xs-5">
                            <div className="row">
                                <div className="col-xs-12">
                                    <div className="row">
                                        <div className="col-xs-12">
                                            <h2>Active Beans' Stock Levels</h2>
                                        </div>
                                    </div>
                                    <div className="row">
                                        <div className="col-xs-12">
                                            {this.state.stockchart ?
                                                <ReactHighcharts config={this.state.stockchart}></ReactHighcharts>
                                                :
                                                <div className="text-center" style={{marginTop: '150px'}}>- Not Available
                                                    - </div>
                                            }
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="row">
                                <div className="col-xs-12">
                                    <h2>Low Stock Alert</h2>
                                </div>
                                <div className="col-xs-12">
                                    <div className="form-group form-inline">
                                        <div className="form-group form-inline">
                                            <p><i className="fa fa-circle" style={{color: 'green'}}></i> - more than <span
                                                style={{fontWeight: 'bold'}}>{this.state.threshold ? 1.5 * this.state.threshold : 0}kg</span>
                                            </p>
                                            <p><i className="fa fa-circle" style={{color: 'orange'}}></i> - more than <span
                                                style={{fontWeight: 'bold'}}>{this.state.threshold ? this.state.threshold : 0}kg</span>
                                            </p>
                                            <p><i className="fa fa-circle" style={{color: 'red'}}></i> - less than <span
                                                style={{fontWeight: 'bold'}}>{this.state.threshold ? this.state.threshold : 0}kg</span>
                                            </p>
                                            <input className="form-control input-sm" defaultValue={this.state.threshold}
                                                   ref="threshold"
                                                   style={{width: '120px'}}/>
                                            <button className="btn btn-primary btn-sm"
                                                    style={{margin: '5px', padding: '5px', width: '120px'}}
                                                    onClick={this.updateThreshold}>Update Threshold
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            );
        }
    })
    ;


module.exports = withRouter(InventoryPage);
