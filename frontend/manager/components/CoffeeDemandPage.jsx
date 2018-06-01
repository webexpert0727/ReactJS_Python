var React = require('react');
var createReactClass = require('create-react-class');
var _ = require('lodash');
var $ = require('jquery');
var withRouter = require('react-router-dom').withRouter;
var ReactCSSTransitionGroup = require('react-addons-css-transition-group');
var RecommendationModal = require('./RecommendationModal');
var ReportCardModal = require('./ReportCardModal');
var moment = require('moment');
const ReactHighcharts = require('react-highcharts');


var CoffeeDemandPage = createReactClass({
        loadCount: 1,
        getInitialState: function () {
            return {loadCount: 0};
        },
        componentDidMount: function () {

            this.getRecommendation();
            this.checkReportCard();
        },
        getRecommendation: function () {
            var csrftoken = '';
            var cookies = document.cookie.split(';');
            _.map(cookies, function (cookie) {
                var keyValue = cookie.split('=');
                if (keyValue[0].trim() == 'csrftoken') {
                    csrftoken = keyValue[1];
                }
                ;
            });

            var ajax = $.ajax({
                url: '/manager/api/getRecommendation',
                beforeSend: function (xhr) {
                    xhr.setRequestHeader('X-CSRFToken', csrftoken);
                },
                method: 'GET',
                dataType: 'json',
                jsonp: false,
                context: this,
                success: function (res) {
                    console.log(res);
                    this.setState({
                        recommendation: _.pick(res, ['statistics', 'actions']),
                        loadCount: this.state.loadCount + 1
                    })

                },
                error: function (e) {
                    console.log(e);
                    this.setState({loadCount: this.state.loadCount + 1});

                }
            });
        },
        checkReportCard: function () {
            var csrftoken = '';
            var cookies = document.cookie.split(';');
            _.map(cookies, function (cookie) {
                var keyValue = cookie.split('=');
                if (keyValue[0].trim() == 'csrftoken') {
                    csrftoken = keyValue[1];
                }
                ;
            });

            // var firstMonth = moment().startOf('YEAR').format('DD-MM-YYYY');
            var firstMonth = moment().add(-6, 'MONTH').format('DD-MM-YYYY');
            var lastMonth = moment().add(-1, 'MONTH').format('DD-MM-YYYY');
            var ajax = $.ajax({
                url: '/manager/api/getReportCard?start_date=' + firstMonth + '&end_date=' + lastMonth,
                beforeSend: function (xhr) {
                    xhr.setRequestHeader('X-CSRFToken', csrftoken);
                },
                method: 'GET',
                dataType: 'json',
                jsonp: false,
                context: this,
                success: function (res) {
                    console.log(res);
                    var reports = res.reports;


                    var z = 51;
                    // var sd = [];
                    var categories = [];
                    var predictcount = [];
                    var actualcount = [];
                    _.each(reports, function (report) {

                        var show_date = moment('01-' + report.date, 'DD-MM-YYYY').format("MMM 'YY");

                        categories.push(show_date);
                        predictcount.push(report.report_card.expected_demand);
                        actualcount.push(report.report_card.demand_actualising);
                        // sd.push(0);

                    });
                    var $this = this;
                    // var clickevent = function (event) {
                    //     console.log(event.point.index);
                    //     var report = reports[event.point.index];
                    //     $this.openReportModal(report);
                    // };

                    var chart = {
                        chart: {
                            // type:'StockChart'
                            height: 230
                        },

                        rangeSelector: {
                            selected: 1
                        },
                        legend: {
                            enabled: true
                        },
                        title: {
                            text: ''
                        },
                        xAxis: {
                            allowDecimals: false,
                            categories: categories,
                            title: {text: 'Past 6 Months'}
                        },
                        yAxis: {
                            allowDecimals: false,
                            title: {text: '% Change'},
                            labels: {
                                formatter: function () {
                                    return this.value + '%';
                                }
                            }
                        },

                        series: [{
                            name: 'Predicted',
                            data: predictcount,
                            color: '#228B22',
                            // events: {
                            //     click: clickevent
                            // },
                            tooltip: {
                                valueDecimals: 0,
                                pointFormatter: function () {
                                    return '<span style="color:' + this.color + '">\u25CF</span> ' + this.series.name + ': <b>' + this.y + '%</b><br/>'
                                }
                            }
                        }, {
                            name: 'Actual',
                            data: actualcount,
                            color: '#755248',
                            tooltip: {
                                valueDecimals: 0,
                                pointFormatter: function () {
                                    return '<span style="color:' + this.color + '">\u25CF</span> ' + this.series.name + ': <b>' + this.y + '%</b><br/>'
                                }
                            },
                            // events: {
                            //     click: clickevent
                            // },
                        },
                            //     {
                            //     name: 'Deviation from recommendation',
                            //     data: sd,
                            //     color: '#000000',
                            //     events: {
                            //         click: clickevent
                            //     },
                            //     tooltip: {
                            //         valueDecimals: 0,
                            //         pointFormatter: function(){
                            //             return '<span style="color:'+ this.color + '">\u25CF</span> ' + this.series.name + ': <b>'+ this.y + '%</b><br/>'
                            //         }
                            //     }
                            // }

                        ]
                    };

                    this.setState({demandchart: chart, reports: res.reports});


                },
                error: function (e) {
                    console.log(e);
                    this.setState({loadCount: this.state.loadCount + 1});
                }
            });
        },
        togglePredictionModal: function () {
            $('#viewPrediction').modal('toggle');
        },
        openReportModal: function (report) {
            console.log(report);
            var date = moment('01-' + report.date, 'DD-MM-YYYY')
            this.setState({report: report, month: date}, function () {
                $('#viewReportCard' + date.format('MMMM')).modal('toggle');
            });
        },
        render: function () {
            var $this = this;


            if (this.state.loadCount < this.loadCount) {
                return (
                    <div className="container">
                        <div className="row" style={{marginTop: '0px', marginBottom: '20px'}}>
                            <div className="col-xs-10 col-xs-offset-1 col-sm-6 col-sm-offset-3">
                                <h1 className="text-center">{moment().format('MMMM')}'s Coffee Demand Prediction</h1>
                            </div>
                        </div>
                        <div style={{textAlign: 'center', marginTop: '130px'}}><i className="fa fa-spinner fa-spin fa-3x"/>
                        </div>
                    </div>
                )
            }


            var actions = null;
            var statistics = null;
            if (this.state.recommendation) {
                actions = this.state.recommendation.actions;
                statistics = this.state.recommendation.statistics;
            }


            var pastMonthsTable = '';
            if (this.state.reports) {
                pastMonthsTable = this.state.reports.map(function (report) {
                    var actions = report.report_card.actions;
                    return (
                        <tr key={report.date} onClick={$this.openReportModal.bind(null, report)}>
                            <td>{moment('01-' + report.date, 'DD-MM-YYYY').format("MMM 'YY")}</td>
                            <td style={{backgroundColor: '#4CAEE2', textAlign: 'center', color: 'white'}}>
                                $ {actions.adwords_cost}</td>
                            <td style={{backgroundColor: '#4359A3', textAlign: 'center', color: 'white'}}>
                                $ {actions.facebook_advertising_cost}</td>
                            <td style={{
                                backgroundColor: '#B9A258',
                                textAlign: 'center',
                                color: 'white'
                            }}>{actions.new_coffees}</td>
                            <td style={{
                                backgroundColor: '#72BBB0',
                                textAlign: 'center',
                                color: 'white'
                            }}>{actions.blog_posts}</td>
                            <td style={{
                                backgroundColor: '#2D9199',
                                textAlign: 'center',
                                color: 'white'
                            }}>{actions.email_campaigns}</td>
                            <td style={{
                                backgroundColor: '#F3776E',
                                textAlign: 'center',
                                color: 'white'
                            }}>{actions.roadshows}</td>
                            <td style={{
                                backgroundColor: 'black',
                                textAlign: 'center',
                                color: 'white'
                            }}>{report.report_card.deviation} %</td>
                            <td style={{fontWeight: 'bold', fontStyle: 'italic'}}>{report.report_card.new_signups}</td>
                            <td style={{fontWeight: 'bold', fontStyle: 'italic'}}>{report.report_card.active_customers}</td>
                            <td style={{fontWeight: 'bold', fontStyle: 'italic'}}>{report.report_card.orders}</td>
                            <td style={{fontWeight: 'bold', fontStyle: 'italic'}}>{report.report_card.churn}</td>
                            <td>{report.report_card.expected_demand.toFixed(2)} %</td>
                            <td>{report.report_card.demand_actualising.toFixed(2)} %</td>
                        </tr>

                    )
                })
            }

            return (
                <div className="container">


                    {this.state.report && this.state.month ?
                        <ReportCardModal report={this.state.report} month={this.state.month}></ReportCardModal> : null}
                    <div className="row">
                        <div className="col-xs-10 col-xs-offset-1 col-sm-6 col-sm-offset-3">
                            <h1 className="text-center">{moment().format('MMMM')}'s Coffee Demand Prediction</h1>
                            {/*<h4 className="text-center">History and Forecast</h4>*/}
                            <br/>
                        </div>
                    </div>
                    <div className="row">
                        <div className="col-xs-12 col-md-12">
                            {this.state.recommendation ?
                                <div className="row">
                                    <div className="col-xs-12 col-md-12">
                                        <div className="row">
                                            <div className="col-xs-4 col-md-4">
                                                <div className="panel" style={{backgroundColor: '#4CAEE2'}}>
                                                    <div className="panel-heading">
                                                        <div className="row">
                                                            <div className="col-xs-12"
                                                                 style={{color: '#FFFFFF', paddingBottom: '10px'}}>
                                                                GOOGLE ADWORDS
                                                            </div>
                                                        </div>
                                                        <div className="row">
                                                            <div className="col-xs-6">

                                                                <img style={{width: '65px', marginLeft: '10px'}}
                                                                     src={STATIC + "images/adwords_logo.png"}
                                                                     className="img"
                                                                     alt="Responsive image"/>
                                                            </div>
                                                            <div className="col-xs-6 text-right">
                                                                <div style={{
                                                                    fontSize: '80px',
                                                                    color: '#FFFFFF',
                                                                    marginTop: '-30px'
                                                                }}>${actions.adwords_cost.toFixed(0)}</div>

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
                                                                 style={{color: '#FFFFFF', paddingBottom: '10px'}}>
                                                                FACEBOOK ADS
                                                            </div>
                                                        </div>
                                                        <div className="row">
                                                            <div className="col-xs-6">
                                                                <i style={{marginLeft: '10px', color: '#FFFFFF'}}
                                                                   className="fa fa-facebook fa-4x"></i>
                                                            </div>
                                                            <div className="col-xs-6 text-right">
                                                                <div style={{
                                                                    fontSize: '80px',
                                                                    color: '#FFFFFF',
                                                                    marginTop: '-30px'
                                                                }}>${actions.facebook_advertising_cost.toFixed(0)}</div>

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
                                                                 style={{color: '#FFFFFF', paddingBottom: '10px'}}>
                                                                NEW COFFEES
                                                            </div>
                                                        </div>
                                                        <div className="row">
                                                            <div className="col-xs-6">

                                                                <i style={{color: '#FFFFFF'}}
                                                                   className="fa fa-coffee fa-4x"></i>
                                                            </div>
                                                            <div className="col-xs-6 text-right">
                                                                <div style={{
                                                                    fontSize: '80px',
                                                                    color: '#FFFFFF',
                                                                    marginTop: '-30px'
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
                                                            <div className="col-xs-12"
                                                                 style={{color: '#FFFFFF', paddingBottom: '10px'}}>BLOG
                                                                ARTICLES
                                                            </div>
                                                        </div>
                                                        <div className="row">
                                                            <div className="col-xs-6">

                                                                <i style={{marginLeft: '10px', color: '#FFFFFF'}}
                                                                   className="fa fa-wordpress fa-4x"></i>
                                                            </div>
                                                            <div className="col-xs-6 text-right">
                                                                <div style={{
                                                                    fontSize: '80px',
                                                                    color: '#FFFFFF',
                                                                    marginTop: '-30px'
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
                                                            <div className="col-xs-12"
                                                                 style={{color: '#FFFFFF', paddingBottom: '10px'}}>EMAIL
                                                                CAMPAIGNS
                                                            </div>
                                                        </div>
                                                        <div className="row">
                                                            <div className="col-xs-6">

                                                                <i style={{marginLeft: '10px', color: '#FFFFFF'}}
                                                                   className="fa fa-envelope fa-4x"></i>
                                                            </div>
                                                            <div className="col-xs-6 text-right">
                                                                <div style={{
                                                                    fontSize: '80px',
                                                                    color: '#FFFFFF',
                                                                    marginTop: '-30px'
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
                                                            <div className="col-xs-12"
                                                                 style={{color: '#FFFFFF', paddingBottom: '10px'}}>
                                                                ROADSHOWS
                                                            </div>
                                                        </div>
                                                        <div className="row">
                                                            <div className="col-xs-6">
                                                                <i style={{marginLeft: '10px', color: '#FFFFFF'}}
                                                                   className="fa fa-shopping-cart fa-4x"></i>
                                                            </div>
                                                            <div className="col-xs-6 text-right">
                                                                <div style={{
                                                                    fontSize: '80px',
                                                                    color: '#FFFFFF',
                                                                    marginTop: '-30px'
                                                                }}>{actions.roadshows.toFixed(0)}</div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="row">
                                            <div style={{textAlign: 'center'}}>
                                                <span style={{fontSize: '1.2em'}}>Estimated demand:</span><span
                                                style={{fontSize: '1.8em'}}> {statistics.expected_demand.toFixed(2)}%</span>
                                            </div>
                                            <div style={{textAlign: 'center'}}>
                                                <span style={{fontSize: '1.2em'}}>Demand actualising:</span><span
                                                style={{fontSize: '1.8em'}}> {statistics.demand_actualising.toFixed(2)}%</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                : null}

                        </div>
                    </div>
                    <br/>
                    <div className="row">
                        <div className="col-xs-12 col-md-12">
                            <h2 className="text-left">Past 6 Months:</h2>
                        </div>
                    </div>
                    <div className="row">
                        {this.state.demandchart ? <ReactHighcharts config={this.state.demandchart}></ReactHighcharts> :
                            <div style={{textAlign: 'center', marginTop: '50px'}}><i
                                className="fa fa-spinner fa-spin fa-3x"/>
                            </div>}
                    </div>
                    <div className="row">
                        <div className="col-xs-12">
                            <table className="table table-hover">
                                <thead>
                                <tr>
                                    <th>Month</th>

                                    <th style={{backgroundColor: '#4CAEE2', color: 'white', textAlign: 'center'}}><img
                                        style={{width: '30px'}} src={STATIC + "images/adwords_logo.png"} className="img"
                                        alt="Responsive image"/></th>
                                    <th style={{
                                        backgroundColor: '#4359A3',
                                        color: 'white',
                                        textAlign: 'center',
                                        width: '50px'
                                    }}><i
                                        className="fa fa-facebook fa-2x"></i></th>
                                    <th style={{
                                        backgroundColor: '#B9A258',
                                        color: 'white',
                                        textAlign: 'center',
                                        width: '50px'
                                    }}><i
                                        className="fa fa-coffee fa-2x"></i></th>
                                    <th style={{
                                        backgroundColor: '#72BBB0',
                                        color: 'white',
                                        textAlign: 'center',
                                        width: '50px'
                                    }}><i
                                        className="fa fa-wordpress fa-2x"></i></th>
                                    <th style={{
                                        backgroundColor: '#2D9199',
                                        color: 'white',
                                        textAlign: 'center',
                                        width: '50px'
                                    }}><i
                                        className="fa fa-envelope fa-2x"></i></th>
                                    <th style={{
                                        backgroundColor: '#F3776E',
                                        color: 'white',
                                        textAlign: 'center',
                                        width: '50px'
                                    }}><i
                                        className="fa fa-shopping-cart fa-2x"></i></th>
                                    <th style={{
                                        backgroundColor: 'black',
                                        color: 'white',
                                        textAlign: 'center',
                                        width: '50px'
                                    }}>Deviation
                                    </th>
                                    <th style={{fontStyle: 'italic'}}>New signups</th>
                                    <th style={{fontStyle: 'italic'}}>Active customers</th>
                                    <th style={{fontStyle: 'italic'}}>Orders</th>
                                    <th style={{fontStyle: 'italic'}}>Churn</th>
                                    <th>Estimated Demand</th>
                                    <th>Demand actualising</th>


                                </tr>
                                </thead>
                                <tbody>
                                {pastMonthsTable}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )
                ;
        }
    })
    ;


module.exports = withRouter(CoffeeDemandPage);
