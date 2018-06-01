import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { connect } from 'react-redux';
import ReactHighcharts from 'react-highcharts';
import HighchartsExporting from 'highcharts-exporting';
import HighchartsExportCSV from 'highcharts-export-csv';

import moment from 'moment';
import _ from 'lodash';
import $ from 'jquery';
import swal from 'sweetalert';
import 'sweetalert/dist/sweetalert.css';

import { ApiRequest, getBeanStatus } from '../../utils';
import { actions as dashboardActions } from '../../reducers/dashboard';
import { ReportCardModal } from '..';

HighchartsExporting(ReactHighcharts.Highcharts);
HighchartsExportCSV(ReactHighcharts.Highcharts);


class DashboardPage extends Component {

  static propTypes = {
    getReportCard: PropTypes.func.isRequired,
    reportCard: PropTypes.object, // eslint-disable-line
  }

  constructor(props) {
    super(props);
    this.loadCount = 12;
    this.moment = moment();
    this.month = moment().add(-1, 'MONTH');
    this.revenueYear = moment();
    this.dates = [
      moment().add(-1, 'WEEK').startOf('week'),
      moment().startOf('week'),
      moment(),
      moment().add(1, 'WEEK').startOf('week'),
    ];
  }

  state = {
    mostPopularCoffees: null,
    loadCount: 0,
    newSignUps: 0,
  }

  componentDidMount() {
    this.getCoffeePerformance();
    this.getActiveBeans();
    this.getVoucherPerformance();
    this.getPercentageCustomersByAge();
    this.getCountOrders(this.moment);
    this.getNewSignups();

    this.getWebsiteViews();
    this.getActiveCustomerBreakdown();
    this.getUserChurnRate();
    this.getLifetimeValue();
    this.getThreshold();
    this.getRevenue(this.revenueYear);
    this.getActiveCustomersByMonth();
    this.getDecayCustomersByMonth();
    this.props.getReportCard(this.month);
  }

  getThreshold = () => {
    var csrftoken = '';
    var cookies = document.cookie.split(';');
    _.map(cookies, function (cookie) {
      var keyValue = cookie.split('=');
      if (keyValue[0].trim() == 'csrftoken') {
        csrftoken = keyValue[1];
      }
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
  }

  getRevenue = (revenueYear) => {
    var csrftoken = '';
    var cookies = document.cookie.split(';');
    _.map(cookies, function (cookie) {
      var keyValue = cookie.split('=');
      if (keyValue[0].trim() == 'csrftoken') {
        csrftoken = keyValue[1];
      }
    });

    var startdate = moment(revenueYear).add(-11, 'MONTH').format('DD-MM-YYYY');
    var enddate = revenueYear.format('DD-MM-YYYY');

    $.ajax({
      url: '/manager/api/revenue?start_date=' + startdate + '&end_date=' + enddate,
      beforeSend: function (xhr) {
        xhr.setRequestHeader('X-CSRFToken', csrftoken);
      },
      method: 'GET',
      dataType: 'json',
      context: this,
      success: function (res) {
        console.log('revenue', res);

        if (res.status == 200) {
          var months = res.months_revenue;

          var monthscount = [];
          var categories = [];

          _.each(months, function (month) {
            var date = month.date;
            var revenue = month.revenue;
            monthscount.push([date, revenue]);

            var show_date = moment('01-' + month.date, 'DD-MM-YYYY').format("MMM 'YY");
            categories.push(show_date);
          });

          var realisedcount = _.clone(monthscount);
          realisedcount.pop();
          realisedcount.push(months[months.length - 1].realised_revenue);


          var chart = {
            chart: {
              // type:'StockChart'
              height: 230,
            },

            rangeSelector: {
              selected: 1,
            },
            legend: {
              enabled: true,
            },
            title: {
              text: '',
            },
            xAxis: {
              allowDecimals: false,
              categories: categories,
              title: {text: 'Past 12 Months'},
            },
            yAxis: {
              allowDecimals: false,
              title: {text: 'Revenue'},
            },

            series: [{
              name: 'Realised Revenue',
              data: realisedcount,
              color: '#228B22',
              tooltip: {
                valueDecimals: 0,
              },
            }, {
              name: 'Revenue',
              data: monthscount,
              color: '#755248',
              tooltip: {
                valueDecimals: 0,
              },
            }],
          };
          this.setState({revenuechart: chart, loadCount: this.state.loadCount + 1});
        } else {
          this.setState({loadCount: this.state.loadCount + 1});
        }
      },
    });
  }

  getActiveCustomersByMonth = () => {
    const chartConfig = months => ({
      chart: { height: 350 },
      title: { text: '' },
      subtitle: { text:
        `
        - Customers - signed up in a month and have at least one shipped order in that month.<br/>
        - Subscribers - the same, but related only for recurrent orders.
        `,
        useHTML: true,
      },
      xAxis: { categories: months.map(m => moment(m.date).format("MMM 'YY")) },
      yAxis: { title: { text: 'Customers' } },
      series: [{
        name: 'Active Customers',
        data: months.map(m => m.customers),
        color: '#755248',
      }, {
        name: 'Active Subscribers',
        data: months.map(m => m.subscribers),
        color: '#228B22',
      }],
    });

    ApiRequest.get('activeCustomersByMonth')
      .then((resp) => {
        this.setState({
          activeCustomersChart: chartConfig(resp.data),
          loadCount: this.state.loadCount + 1,
        });
      })
      .catch((err) => {
        swal({ title: err, type: 'error' });
        this.setState({ loadCount: this.state.loadCount + 1 });
      });
  }

  getDecayCustomersByMonth = () => {
    const chartConfig = (months, conf) => ({
      chart: { type: 'area', height: 600 },
      title: { text: '' },
      subtitle: { text: conf.text, useHTML: true },
      xAxis: { type: 'datetime' },
      yAxis: { title: { text: 'Customers' } },
      plotOptions: {
        area: {
          stacking: 'normal',
          lineColor: '#666666',
          lineWidth: 1,
          marker: {
            enabled: false,
            symbol: 'circle',
            radius: 2,
            states: {
              hover: {
                enabled: true,
              },
            },
          },
        },
      },
      series: months.map(month => ({
        name: `Reg at ${moment(month.signed_up).format("MMM 'YY")}`,
        data: month.data.map(m => [m.ts, m[conf.field]]),
        tooltip: { headerFormat: '' },
      })),
    });

    const strictChart = {
      field: 'customers',
      text: `Strict sampling of active customers.<br/>
             Consider a customer is active if there was at least
             one shipped recurrent order in a month.`,
    };
    const notStrictChart = {
      field: 'customers_not_strict',
      text: `Not strict sampling of active customers.<br/>
             Consider a customer is active all the time between the first and 
             last recurrent orders.`,
    };

    ApiRequest.get('decayCustomersByMonth')
      .then((resp) => {
        this.setState({
          decayCustomersChart: chartConfig(resp.data, strictChart),
          decayCustomersChartNotStrict: chartConfig(resp.data, notStrictChart),
          loadCount: this.state.loadCount + 1,
        });
      })
      .catch((err) => {
        swal({ title: err, type: 'error' });
        this.setState({ loadCount: this.state.loadCount + 1 });
      });
  }

  getCoffeePerformance = () => {
    var csrftoken = '';
    var cookies = document.cookie.split(';');
    _.map(cookies, function (cookie) {
      var keyValue = cookie.split('=');
      if (keyValue[0].trim() == 'csrftoken') {
        csrftoken = keyValue[1];
      }
    });

    var startdate = moment().startOf('month').format('DD-MM-YYYY');
    var enddate = moment().endOf('month').format('DD-MM-YYYY');

    console.log(startdate, enddate);
    $.ajax({
      url: '/manager/api/coffeePerformance?start_date=' + startdate + '&end_date=' + enddate,
      beforeSend: function (xhr) {
        xhr.setRequestHeader('X-CSRFToken', csrftoken);
      },
      method: 'GET',
      dataType: 'json',
      context: this,
      success: function (res) {
        console.log(res);
        if (res.status == 500) {
          this.setState({loadCount: this.state.loadCount + 1});
          return;
        }
        this.setState({mostPopularCoffees: res.coffee_performance, loadCount: this.state.loadCount + 1});
      },
      error: function (e) {
        console.log(e);
        this.setState({loadCount: this.state.loadCount + 1});
      },
    });
  }

  getActiveBeans = () => {
    var csrftoken = '';
    var cookies = document.cookie.split(';');
    _.map(cookies, function (cookie) {
      var keyValue = cookie.split('=');
      if (keyValue[0].trim() == 'csrftoken') {
        csrftoken = keyValue[1];
      }
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
        this.setState({beans: sorted_beans, loadCount: this.state.loadCount + 1});
      },
    });
  }

  getVoucherPerformance = () => {
    var csrftoken = '';
    var cookies = document.cookie.split(';');
    _.map(cookies, function (cookie) {
      var keyValue = cookie.split('=');
      if (keyValue[0].trim() == 'csrftoken') {
        csrftoken = keyValue[1];
      }
    });

    var startdate = moment().startOf('month').format('DD-MM-YYYY');
    var enddate = moment().endOf('month').format('DD-MM-YYYY');

    console.log(startdate, enddate);
    $.ajax({
      url: '/manager/api/voucherPerformance?start_date=' + startdate + '&end_date=' + enddate,
      beforeSend: function (xhr) {
        xhr.setRequestHeader('X-CSRFToken', csrftoken);
      },
      method: 'GET',
      dataType: 'json',
      context: this,
      success: function (res) {
        console.log(res);
        if (res.status == 500) {
          this.setState({loadCount: this.state.loadCount + 1});
          return;
        }
        var vouchers = _.slice(res.voucher_performance, 0, 5);
        console.log('vouchers', vouchers);

        var data = null;
        if (vouchers.length > 0) {
          data = [];
          _.each(vouchers, function (voucher) {
              data.push([voucher.voucher_name, voucher.count]);
          });
        }
        console.log('DATAA', data);

        var chart = {
          chart: {
            type: 'column',
          },
          title: {
            text: null,
          },
          subtitle: {
            text: null,
          },
          colors: ['#587F6C'],
          xAxis: {
            type: 'category',
            labels: {
              rotation: -45,
              style: {
                fontSize: '13px',
                fontFamily: 'Verdana, sans-serif',
              },
            },
          },
          yAxis: {
            min: 0,
            title: {
              text: 'No. of vouchers used',
            },
          },
          legend: {
            enabled: false,
          },
          tooltip: {
            pointFormat: 'No. of vouchers used: <b>{point.y}</b>',
          },
          series: [{
            name: 'Voucher codes',
            data: data,
            dataLabels: {
              enabled: true,
              rotation: -90,
              color: '#FFFFFF',
              align: 'right',
              y: 10, // 10 pixels down from the top
              style: {
                fontSize: '13px',
                fontFamily: 'Verdana, sans-serif',
              },
            },
          }],
        };
        this.setState({voucherchart: data ? chart : null, loadCount: this.state.loadCount + 1});
      },
      error: function (e) {
        console.log(e);
        this.setState({loadCount: this.state.loadCount + 1});
      },
    });
  }

  getNewSignups = () => {
    var csrftoken = '';
    var cookies = document.cookie.split(';');
    _.map(cookies, function (cookie) {
      var keyValue = cookie.split('=');
      if (keyValue[0].trim() == 'csrftoken') {
        csrftoken = keyValue[1];
      }
    });

    $.ajax({
      url: '/manager/api/newSignups',
      beforeSend: function (xhr) {
        xhr.setRequestHeader('X-CSRFToken', csrftoken);
      },
      method: 'GET',
      dataType: 'json',
      context: this,
      success: function (res) {
        console.log(res);

        if (res.status == 500) {
          this.setState({loadCount: this.state.loadCount + 1});
          return;
        }

        var oneoff = res.count.one_off;
        var recurring = res.count.recurring;
        this.setState({
          newSignUps: {oneoff: oneoff, recurring: recurring},
          loadCount: this.state.loadCount + 1
        });
      },
      error: function (e) {
        console.log(e);
        this.setState({loadCount: this.state.loadCount + 1});
      },
    });
  }

  getWebsiteViews = () => {
    var csrftoken = '';
    var cookies = document.cookie.split(';');
    _.map(cookies, function (cookie) {
      var keyValue = cookie.split('=');
      if (keyValue[0].trim() == 'csrftoken') {
        csrftoken = keyValue[1];
      }
    });
    $.ajax({
      url: '/manager/api/usersFromGA?start_date=' + moment().add(-1, 'day').format('DD-MM-YYYY') + '&end_date=' + moment().format('DD-MM-YYYY'),
      beforeSend: function (xhr) {
        xhr.setRequestHeader('X-CSRFToken', csrftoken);
      },
      method: 'GET',
      dataType: 'json',
      context: this,
      success: function (res) {
        console.log(res);
        if (res.status == 500) {
          this.setState({loadCount: this.state.loadCount + 1});
          return;
        }
        this.setState({loadCount: this.state.loadCount + 1, websiteViews: res.users});
      },
      error: function (e) {
        console.log(e);
        this.setState({loadCount: this.state.loadCount + 1});
      },
    });
  }

  getLifetimeValue = () => {
    var csrftoken = '';
    var cookies = document.cookie.split(';');
    _.map(cookies, function (cookie) {
      var keyValue = cookie.split('=');
      if (keyValue[0].trim() == 'csrftoken') {
        csrftoken = keyValue[1];
      }
    });
    $.ajax({
      url: '/manager/api/lifetimeValue',
      beforeSend: function (xhr) {
        xhr.setRequestHeader('X-CSRFToken', csrftoken);
      },
      method: 'GET',
      dataType: 'json',
      context: this,
      success: function (res) {
        console.log(res);
        if (res.status == 500) {
          this.setState({loadCount: this.state.loadCount + 1});
          return;
        }
        var lifetime_value = res.lifetime_value;
        this.setState({loadCount: this.state.loadCount + 1, lifetimevalue: lifetime_value});
      },
      error: function (e) {
        console.log(e);
        this.setState({loadCount: this.state.loadCount + 1});
      },
    });
  }

  getActiveCustomerBreakdown = () => {
    var csrftoken = '';
    var cookies = document.cookie.split(';');
    _.map(cookies, function (cookie) {
      var keyValue = cookie.split('=');
      if (keyValue[0].trim() == 'csrftoken') {
        csrftoken = keyValue[1];
      }
    });

    $.ajax({
      url: '/manager/api/activeCustomerBreakdown',
      beforeSend: function (xhr) {
        xhr.setRequestHeader('X-CSRFToken', csrftoken);
      },
      method: 'GET',
      dataType: 'json',
      context: this,
      success: function (res) {
        console.log(res);

        if (res.status == 500) {
          this.setState({loadCount: this.state.loadCount + 1});
          return;
        }

        var breakdown = res.customer_breakdown;
        var data = [{
          name: 'Active: ' + breakdown.active.toFixed(0) + '%',
          y: breakdown.active,
        }, {
          name: 'Inactive (1 month): ' + breakdown.inactive_one_month.toFixed(0) + '%',
          y: breakdown.inactive_one_month,
        }, {
          name: 'Inactive (3 months): ' + breakdown.inactive_three_month.toFixed(0) + '%',
          y: breakdown.inactive_three_month,
        }, {
          name: 'Inactive (6 months): ' + breakdown.inactive_six_month.toFixed(0) + '%',
          y: breakdown.inactive_six_month,
        }];

        var chart = {
          chart: {
            plotBackgroundColor: null,
            plotBorderWidth: null,
            plotShadow: false,
            type: 'pie',
          },
          title: {
            text: null,
          },
          colors: ['#5A7F68', '#FFECCE', '#BFB19A', '#7F7667'],
          tooltip: {
            pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>',
          },
          plotOptions: {
            pie: {
              allowPointSelect: true,
              cursor: 'pointer',
              dataLabels: {
                enabled: false,
              },
              showInLegend: true,
            },
          },
          series: [{
            name: 'Subscribers',
            colorByPoint: true,
            data: data,
          }],
        };
      this.setState({loadCount: this.state.loadCount + 1, subscriberchart: chart});
      },
      error: function (e) {
        console.log(e);
        this.setState({loadCount: this.state.loadCount + 1});
      },
    });
  }

  getUserChurnRate = () => {
    var csrftoken = '';
    var cookies = document.cookie.split(';');
    _.map(cookies, function (cookie) {
      var keyValue = cookie.split('=');
      if (keyValue[0].trim() == 'csrftoken') {
        csrftoken = keyValue[1];
      }
    });

    $.ajax({
      url: '/manager/api/userChurnRate',
      beforeSend: function (xhr) {
        xhr.setRequestHeader('X-CSRFToken', csrftoken);
      },
      method: 'GET',
      dataType: 'json',
      context: this,
      success: function (res) {
        console.log(res);

        if (res.status == 500) {
          this.setState({loadCount: this.state.loadCount + 1});
          return;
        }

        var breakdown = res.churn_rate_breakdown;
        var categories = [];
        var data = [];

        // _.each(breakdown, function(month){
        //     categories.push(month.month);
        //     data.push(month.rate);
        // })
        var reversed_breakdown = _.reverse(_.slice(breakdown, 0, 6));


        for (var i = 0; i < 6; i++) {
          var month = reversed_breakdown[i];
          if (month) {
            categories.push(month.month);
            data.push(parseFloat(month.rate.toFixed(2)));
            // console.log(month.rate.toFixed(2), month.rate);
          }
        }
        console.log(data);

        var chart = {
          chart: {
            type: 'line',
          },
          title: {
            text: null,
          },
          subtitle: {
            text: null,
          },
          colors: ['#1C434D'],
          xAxis: {
            categories: categories,
          },
          yAxis: {
            title: {
              text: 'No. of Customers Who Unsubscribed',
            },
          },
          plotOptions: {
            line: {
              dataLabels: {
                enabled: true,
              },
              enableMouseTracking: false,
            },
          },
          series: [{
            name: 'Unsubscribed',
            data: data,
          }],
        };
        this.setState({loadCount: this.state.loadCount + 1, churnchart: chart});
      },
      error: function (e) {
        console.log(e);
        this.setState({loadCount: this.state.loadCount + 1});
      },
    });
  }

  getPercentageCustomersByAge = () => {
    var csrftoken = '';
    var cookies = document.cookie.split(';');
    _.map(cookies, function (cookie) {
      var keyValue = cookie.split('=');
      if (keyValue[0].trim() == 'csrftoken') {
        csrftoken = keyValue[1];
      }
    });

    $.ajax({
      url: '/manager/api/percentageCustomersByAge',
      beforeSend: function (xhr) {
        xhr.setRequestHeader('X-CSRFToken', csrftoken);
      },
      method: 'GET',
      dataType: 'json',
      context: this,
      success: function (res) {
        console.log(res);

        if (res.status == 500) {
          this.setState({loadCount: this.state.loadCount + 1});
          return;
        }

        var customers = res.customer_percentage_by_age;

        // var data = [];
        var data = [{}, {}, {}, {}, {}];

        _.each(customers, function (customer) {
          var type = customer.type;
          type = type.replace('<', 'less than');
          type = type.replace('>', 'more than');
          var index = -1;
          if (type == 'less than 1 month') {
            index = 0;
          } else if (type == '1 - 3 months') {
            index = 1;
          } else if (type == '3 - 6 months') {
            index = 2;
          } else if (type == '6 - 12 months') {
            index = 3;
          } else if (type == 'more than 12 months') {
            index = 4;
          }
          data[index].name = type + ': ' + customer.count.toFixed(0) + '%';
          data[index].y = customer.count;
        });
        console.log(data);
        var chart = {
          chart: {
            plotBackgroundColor: null,
            plotBorderWidth: null,
            plotShadow: false,
            type: 'pie',
          },
          title: {
            text: null,
          },
          colors: ['#495766', '#778DA6', '#AECEF2', '#DEEFFF'],
          tooltip: {
            pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>',
          },
          plotOptions: {
            pie: {
              allowPointSelect: true,
              cursor: 'pointer',
              dataLabels: {
                enabled: false,
              },
              showInLegend: true,
            },
          },
          series: [{
            name: '% of Customers',
            colorByPoint: true,
            data: data,
          }],
        };
        this.setState({retentionchart: chart, loadCount: this.state.loadCount + 1});
      },
      error: function (e) {
        console.log(e);
        this.setState({loadCount: this.state.loadCount + 1});
      },
    });
  }

  getCountOrders = (moment) => {
    var csrftoken = '';
    var cookies = document.cookie.split(';');
    _.map(cookies, function (cookie) {
      var keyValue = cookie.split('=');
      if (keyValue[0].trim() == 'csrftoken') {
        csrftoken = keyValue[1];
      }
    });

    var startdate = moment.startOf('week').format('DD-MM-YYYY');
    var enddate = moment.endOf('week').format('DD-MM-YYYY');
    console.log(startdate, enddate);
    var data = {
      startdate: startdate,
      enddate: enddate,
      type: ['Aeropress', 'Drip', 'Espresso', 'French press', 'Stove top', 'None'],
    };
    $.ajax({
      url: '/manager/api/orderCount/',
      beforeSend: function (xhr) {
        xhr.setRequestHeader('X-CSRFToken', csrftoken);
      },
      method: 'POST',
      data: JSON.stringify(data),
      dataType: 'json',
      context: this,
      success: function (res) {
        console.log(res);

        if (res.status == 500) {
          this.setState({loadCount: this.state.loadCount + 1});
          return;
        }

        var orders = res.orders;
        var orderscount = [];
        var categories = [];
        _.each(orders, function (value, key) {
          var dateArr = key.split('-');
          var date = dateArr[2] + '-' + dateArr[1] + '-' + dateArr[0];
          orderscount.push([date, value]);
          categories.push(date);
        });

        var chart = {
          chart: {
            // type:'StockChart'
            height: 230,
          },
          rangeSelector: {
            selected: 1,
          },
          legend: {
            enabled: false,
          },
          title: {
            text: '',
          },
          xAxis: {
            allowDecimals: false,
            categories: categories,
            title: {text: 'Week'},
          },
          yAxis: {
            allowDecimals: false,
            title: {text: 'Orders Count'},
          },
          series: [{
            name: 'coffee orders',
            data: orderscount,
            color: '#755248',
            tooltip: {
              valueDecimals: 0,
            },
          }],
        };
        this.setState({coffeechart: chart, loadCount: this.state.loadCount + 1});
      },
      error: function (e) {
        console.log(e);
        this.setState({loadCount: this.state.loadCount + 1});
      },
    });
  }

  adjustWeek = (adjustment) => {
    this.moment.add(adjustment, 'WEEK');
    this.getCountOrders(this.moment);
  }

  adjustRevenueYear = (adjustment) => {
    this.revenueYear.add(adjustment, 'YEAR');
    this.getRevenue(this.revenueYear);
  }

  render() {
    if (this.state.loadCount < this.loadCount) {
      return (
        <div className="container">
          <div className="row" style={{marginTop: '0px', marginBottom: '20px'}}>
            <div className="col-xs-10 col-xs-offset-1 col-sm-6 col-sm-offset-3">
              <h1 className="text-center">Dashboard</h1>
            </div>
          </div>
          <div style={{textAlign: 'center', marginTop: '130px'}}><i className="fa fa-spinner fa-spin fa-3x"/>
          </div>
        </div>
      );
    }
    var beansHtml = null;
    var $this = this;
    if (this.state.beans && this.state.beans.length > 0) {
      beansHtml = this.state.beans.map(function (bean) {
        var currStock = bean.weeks[2].stock;
        var roast = bean.estimated_amount_to_roast;
        var estimatedStock = currStock - roast;
        var status = getBeanStatus(estimatedStock, $this.state.threshold);

        return (
          <tr key={bean.bean_id}>
            <td><i className="fa fa-circle" style={{color: status}}></i></td>
            <td>
              {bean.bean_name}
            </td>
            <td>{bean.weeks[2].stock}</td>
          </tr>
        )
      });
    }

    const reportCard = this.props.reportCard;
    const hasReportCard = reportCard && Object.keys(reportCard).length > 0;
    if (hasReportCard && !reportCard.report_card.actions.blog_posts) {
      $(`#viewReportCard${this.month.format('MMMM')}`).modal('show');
    }
    return (
      <div className="container-fluid">
        {hasReportCard &&
          <ReportCardModal report={reportCard} month={this.month} />}

        <div className="row">
          <div className="col-xs-12 col-md-12">

            {/*TOP ROW*/}
            <div className="row">
              <div className="col-xs-12 col-md-3"
                 style={{ backgroundColor: '#F7EEE9', height: '130px', marginTop: '10px' }}>
                <h3 className="header3 text-center" style={{paddingTop: '5px'}}>New Signups Since Yesterday:</h3>
                <div className="row">
                  <div className="col-xs-6" style={{backgroundColor: '#F7EEE9'}}>
                    <h2 className=" text-center"
                      style={{
                        color: '#5B4E49',
                        marginTop: '5px'
                      }}>{this.state.newSignUps && this.state.newSignUps.oneoff >= 0 ? this.state.newSignUps.oneoff : '-'}<span
                      style={{fontSize: '0.6em'}}>  One-offs</span></h2>
                  </div>
                  <div className="col-xs-6" style={{backgroundColor: '#F7EEE9'}}>
                    <h2 className="header2 text-center"
                      style={{
                        color: '#5B4E49',
                        marginTop: '5px'
                      }}>{this.state.newSignUps && this.state.newSignUps.recurring >= 0 ? this.state.newSignUps.recurring : '-'}<span
                      style={{fontSize: '0.6em'}}>  Subscriptions</span></h2>
                  </div>
                </div>
              </div>
              <div className="col-xs-12 col-md-3"
                 style={{backgroundColor: '#E5DDD9', height: '130px', marginTop: '10px'}}>
                <h3 className="header3 text-center" style={{paddingTop: '5px'}}>{moment().format('MMM')}'s Most Popular Coffee:</h3>
                <h2 className="header2 text-center" style={{paddingBottom: '5px', color: '#5B4E49'}}>
                  {this.state.mostPopularCoffees && this.state.mostPopularCoffees[0] ? this.state.mostPopularCoffees[0].coffee : '-'}</h2>
              </div>
              <div className="col-xs-12 col-md-3"
                 style={{backgroundColor: '#F7EEE9', height: '130px', marginTop: '10px'}}>
                <h3 className="header3 text-center" style={{paddingTop: '5px'}}>Website Views Since Yesterday:</h3>
                <h2 className="header2 text-center" style={{paddingBottom: '5px', color: '#5B4E49'}}>
                    {this.state.websiteViews ? this.state.websiteViews : '-'}</h2>
              </div>

              <div className="col-xs-12 col-md-3"
                 style={{backgroundColor: '#E5DDD9', height: '130px', marginTop: '10px'}}>
                <h3 className="header3 text-center" style={{paddingTop: '5px'}}>Customer Lifetime Value:</h3>
                <h2 className="header2 text-center" style={{paddingBottom: '5px', color: '#5B4E49'}}>
                    $ {this.state.lifetimevalue ? this.state.lifetimevalue.toFixed(2) : '-'}</h2>
              </div>
            </div>

             {/*SECOND ROW*/}
            <div className="row">
              <div className="col-xs-12 col-md-6">
                <h2 className="text-center">Coffee Orders for the week
                  <button className="btn btn-primary btn-sm" style={{marginLeft: '10px'}}
                          onClick={this.adjustWeek.bind(null, -1)}>{'<<'} Prev Week
                  </button>
                  <button className="btn btn-primary btn-sm" style={{marginLeft: '5px'}}
                          onClick={this.adjustWeek.bind(null, 1)}>Next Week {'>>'}</button>
                </h2>
                {this.state.coffeechart
                  ? <ReactHighcharts config={this.state.coffeechart}></ReactHighcharts>
                  : <div className="text-center" style={{marginTop: '130px'}}>- Not available - </div>
                }
              </div>

              <div className="col-xs-12 col-md-6">
                <h2 className="text-center">Customer Churn Rate Tracker</h2>
                {this.state.churnchart
                  ? <ReactHighcharts config={this.state.churnchart}></ReactHighcharts>
                  : <div className="text-center" style={{marginTop: '130px'}}>- Not Available - </div>
                }
              </div>
            </div>

             {/*THIRD ROW*/}
            <div className="row">
              <div className="col-xs-12 col-md-3">
                <h2 className="text-center">{moment().format('MMM')}'s Top 5 Voucher</h2>
                {this.state.voucherchart
                  ? <ReactHighcharts config={this.state.voucherchart}></ReactHighcharts>
                  : <div className="text-center" style={{marginTop: '130px'}}>- No Voucher Usage - </div>
                }
              </div>
              <div className="col-xs-12 col-md-3">
                <h2 className="text-center">Customer Retention Rate</h2>
                {this.state.retentionchart
                  ? <ReactHighcharts config={this.state.retentionchart}></ReactHighcharts>
                  : <div className="text-center" style={{marginTop: '130px'}}>- Not Available - </div>
                }
              </div>

              <div className="col-xs-12 col-md-3">
                <h2 className="text-center">Subscribers</h2>
                {this.state.subscriberchart
                  ? <ReactHighcharts config={this.state.subscriberchart}></ReactHighcharts>
                  : <div className="text-center" style={{marginTop: '130px'}}>- Not Available - </div>
                }
              </div>
              <div className="col-xs-12 col-md-3">
                <h2 className="text-center">Inventory Health</h2>

                {beansHtml
                  ? (
                    <table className="table table-hover">
                      <thead>
                        <tr>
                          <th></th>
                          <th>Active Beans</th>
                          <th>Next week (kg)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {beansHtml}
                      </tbody>
                    </table>)
                  : <div className="text-center" style={{ marginTop: '130px' }}>- No Active Beans - </div>
                }
              </div>
            </div>

            {/*FOURTH ROW*/}
            <div className="row">
              <div className="col-xs-12 col-md-12">
                <h2 className="text-center">Revenue</h2>
                  {/*
                    <button className="btn btn-primary btn-sm" style={{marginLeft: '10px'}}
                    onClick={this.adjustRevenueYear.bind(null, -1)}>{'<<'} Prev Year
                    </button>
                    <button className="btn btn-primary btn-sm" style={{marginLeft: '5px'}}
                    onClick={this.adjustRevenueYear.bind(null, 1)}>Next Year {'>>'}</button>*/
                  }

                {this.state.revenuechart
                  ? <ReactHighcharts config={this.state.revenuechart} />
                  : <div className="text-center" style={{ marginTop: '130px' }}>- Not available -</div>
                }
              </div>
            </div>

            <div className="row">
              <div className="col-xs-12 col-md-12">
                <h2 className="text-center">Active Customers</h2>

                {this.state.activeCustomersChart
                  ? <ReactHighcharts config={this.state.activeCustomersChart} />
                  : <div className="text-center" style={{ marginTop: '130px' }}>- Not available -</div>
                }
              </div>
            </div>

            <div className="row">
              <div className="col-xs-12 col-md-12">
                <h2 className="text-center">Decay Customers</h2>

                {this.state.decayCustomersChart
                  ? <ReactHighcharts config={this.state.decayCustomersChart} />
                  : <div className="text-center" style={{ marginTop: '130px' }}>- Not available -</div>
                }
              </div>
            </div>

            <div className="row">
              <div className="col-xs-12 col-md-12">
                <h2 className="text-center">Decay Customers [Not Strict sampling]</h2>

                {this.state.decayCustomersChartNotStrict
                  ? <ReactHighcharts config={this.state.decayCustomersChartNotStrict} />
                  : <div className="text-center" style={{ marginTop: '130px' }}>- Not available -</div>
                }
              </div>
            </div>

          </div>
        </div>
      </div>
    );
  }
}


const mapStateToProps = state => ({ ...state.dashboard });

const mapDispatchToProps = dispatch => ({
  getReportCard: month => dispatch(dashboardActions.getReportCard(month)),
});


export default withRouter(connect(
  mapStateToProps,
  mapDispatchToProps,
)(DashboardPage));
