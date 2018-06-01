var React = require('react');
var createReactClass = require('create-react-class');
var _ = require('lodash');
var $ = require('jquery');
var withRouter = require('react-router-dom').withRouter;

var d3 = require('d3');
var d3plus = require('d3plus');

var ReactCSSTransitionGroup = require('react-addons-css-transition-group');
var RecommendationModal = require('./RecommendationModal');
var ReportCardModal = require('./ReportCardModal');
var moment = require('moment');

var OverlayTrigger = require('react-bootstrap/lib/OverlayTrigger');
var Popover = require('react-bootstrap/lib/Popover');
var Tooltip = require('react-bootstrap/lib/Tooltip');


var CustomerSegmentationPage = createReactClass({
        loadCount: 0,
        getInitialState: function () {
            return {loadCount: 0, size: 'number_of_customers'};
        },
        componentDidMount: function () {
            this.getCustomerSegments();
        },
        getCustomerSegments: function () {
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
            var ajax = $.ajax({
                url: '/manager/api/getCustomerSegments',
                beforeSend: function (xhr) {
                    xhr.setRequestHeader('X-CSRFToken', csrftoken);
                },
                method: 'GET',
                dataType: 'json',
                jsonp: false,
                context: this,
                success: function (res) {
                    console.log(res);

                    var totalSize = 0;
                    var totalInterval = 0;
                    var totalOneOffOrders = 0;
                    var totalOrders = 0;
                    var totalRatioAmountTime = 0;
                    var totalSpending = 0;
                    var totalVouchers = 0;
                    _.map(res.clusters, function (cluster) {
                        totalSize += cluster.customers.length
                        totalInterval += cluster.mean_interval;
                        totalOneOffOrders += cluster.mean_one_off_orders;
                        totalOrders += cluster.mean_orders;
                        totalRatioAmountTime += cluster.mean_ratio_amount_time;
                        totalSpending += cluster.mean_total_spending;
                        totalVouchers += cluster.mean_vouchers_used;
                    });
                    this.stats = {
                        totalSize: totalSize,
                        totalInterval: totalInterval,
                        totalOneOffOrders: totalOneOffOrders,
                        totalOrders: totalOrders,
                        totalRatioAmountTime : totalRatioAmountTime,
                        totalSpending: totalSpending,
                        totalVouchers: totalVouchers
                    };

                    this.renderChart(res.clusters);
                    this.setState({clusters: res.clusters});
                },
                error: function (e) {
                    console.log(e);
                    this.setState({loadCount: this.state.loadCount + 1});
                }
            });
        },
        renderChart: function (clusters) {

            var data = [];
            $this = this;
            _.map(clusters, function (cluster) {
                cluster.group = 'Customers';
                cluster.size = cluster.customers.length;

                cluster.show_size = cluster.size + ' ' + cluster.cluster_name + ' (' + (cluster.size / $this.stats.totalSize * 100).toFixed(0) + '%)';
                cluster.show_mean_interval = cluster.cluster_name + ' (' + (cluster.mean_interval / $this.stats.totalInterval * 100).toFixed(0) + '%)';
                cluster.show_mean_one_off_orders = cluster.cluster_name + ' (' + (cluster.mean_one_off_orders / $this.stats.totalOneOffOrders * 100).toFixed(0) + '%)';
                cluster.show_mean_orders = cluster.cluster_name + ' (' + (cluster.mean_orders / $this.stats.totalOrders * 100).toFixed(0) + '%)';
                cluster.show_mean_ratio_amount_time = cluster.cluster_name + ' (' + (cluster.mean_ratio_amount_time / $this.stats.totalRatioAmountTime * 100).toFixed(0) + '%)';
                cluster.show_mean_total_spending = cluster.cluster_name + ' (' + (cluster.mean_total_spending / $this.stats.totalSpending * 100).toFixed(0) + '%)';
                cluster.show_mean_vouchers_used = cluster.cluster_name + ' (' + (cluster.mean_vouchers_used / $this.stats.totalVouchers * 100).toFixed(0) + '%)';
                // cluster.show_size = cluster.cluster_name + ' (' + share.toFixed(0) + '%)';

                data.push(cluster);
            });

            // sample data array
            // var sample_data = [
            //     {"value": 100, "name": "alpha", "group": "group 1"},
            //     {"value": 70, "name": "beta", "group": "group 2"},
            //     {"value": 40, "name": "gamma", "group": "group 2"},
            //     {"value": 15, "name": "delta", "group": "group 2"},
            //     {"value": 5, "name": "epsilon", "group": "group 1"},
            //     {"value": 1, "name": "zeta", "group": "group 1"}
            // ]


            // var data = [
            //     {group: 'Customers', value: 60, 'name': 'A'},
            //     {group: 'Customers', value: 60, 'name': 'B'},
            //     {group: 'Customers', value: 100, 'name': 'C'},
            //     {group: 'Customers', value: 70, 'name': 'D'},
            //     {group: 'Customers', value: 60, 'name': 'E'},
            // ]
            // instantiate d3plus

            var visualization = d3plus.viz()
                .container("#viz")     // container DIV to hold the visualization
                .data(data)     // data to use with the visualization
                .type("tree_map")       // visualization type
                .id(["group", "show_size"]) // nesting keys
                .depth(1)              // 0-based depth
                .size("size")         // key name to size bubbles
                .color("cluster_description")        // color by each group
                // .tooltip(['mean_interval', 'mean_one_off_orders', 'mean_orders', 'mean_ratio_amount_time', 'mean_total_spending', 'mean_vouchers_used'])
                .tooltip({
                    value: [],
                    share: false,
                    size: false,
                    sub: 'cluster_description'
                })
                .legend(false)
                .font({"family": "Amatic-Bold"})
                //     .labels({"align": "center", "valign": "bottom"})
                .draw()                // finally, draw the visualization!


            this.vis = visualization;

        },
        reRenderChart: function (size) {
            this.vis.size(size).id(["group", 'show_' + size]).draw();
        },
        handleChangeSize: function (event) {
            var newSize = event.target.value;

            this.setState({size: newSize});
            this.reRenderChart(newSize);


        },
        render: function () {

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

// var intervalPopover = ''
            var intervalTooltip = <Tooltip id="intervalTooltip">Average number of days between each order</Tooltip>;
            var oneOffTooltip = <Tooltip id="oneOffTooltip">Average number of one-off orders</Tooltip>;
            var ordersTooltip = <Tooltip id="ordersTooltip">Average number of orders</Tooltip>;
            var clfTooltip = <Tooltip id="clfTooltip">Customer lifetime value (comparing amount spent against
                time)</Tooltip>;
            var spendingTooltip = <Tooltip id="spendingTooltip">Average total spending</Tooltip>;
            var vouchersTooltip = <Tooltip id="vouchersTooltip">Average number of vouchers used</Tooltip>;
            var mailChimpTooltip = <Tooltip id="mailChimpTooltip">Go to MailChimp</Tooltip>;

            var clustersTableHtml = '';
            if (this.state.clusters) {

                var colors = ['rgb(143, 27, 0)', 'rgb(32, 37, 86)', 'rgb(188, 166, 50)'];
                var mailChimpUrls = ['https://us12.admin.mailchimp.com/lists/members/?id=281333#p:1-s:10-so:null',
                    'https://us12.admin.mailchimp.com/lists/members/?id=281337#p:1-s:10-so:null',
                    'https://us12.admin.mailchimp.com/lists/members/?id=281341#p:1-s:10-so:null'];
                clustersTableHtml = this.state.clusters.map(function (cluster, index) {

                    return (
                        <div className="col-xs-4" key={cluster.cluster_name}>
                            <div style={{background: colors[index], color: '#eeeeee', padding: '4%'}}>
                                <h3 style={{color: 'white'}}>{cluster.size} {cluster.cluster_name} <a href={mailChimpUrls[index]} target="_blank" style={{color:'white'}}><i className="glyphicon glyphicon-envelope" style={{float:'right',cursor:'pointer'}}></i></a></h3>
                                <table className="table">
                                    <tbody>
                                    <tr style={{color: '#eeeeee'}}>
                                        <td><OverlayTrigger trigger={['hover', 'focus']} placement="left"
                                                            overlay={intervalTooltip}><span>Interval: </span></OverlayTrigger>
                                        </td>
                                        <td><OverlayTrigger trigger={['hover', 'focus']} placement="left"
                                                            overlay={intervalTooltip}><span>{cluster.mean_interval}
                                            days</span></OverlayTrigger></td>
                                    </tr>
                                    <tr style={{color: '#eeeeee'}}>
                                        <td><OverlayTrigger trigger={['hover', 'focus']} placement="left"
                                                            overlay={oneOffTooltip}><span>One-off orders:</span></OverlayTrigger>
                                        </td>
                                        <td><OverlayTrigger trigger={['hover', 'focus']} placement="left"
                                                            overlay={oneOffTooltip}><span> {cluster.mean_one_off_orders}
                                            bags</span></OverlayTrigger></td>
                                    </tr>
                                    <tr style={{color: '#eeeeee'}}>
                                        <td><OverlayTrigger trigger={['hover', 'focus']} placement="left"
                                                            overlay={ordersTooltip}><span>Orders:</span></OverlayTrigger>
                                        </td>
                                        <td><OverlayTrigger trigger={['hover', 'focus']} placement="left"
                                                            overlay={ordersTooltip}><span> {cluster.mean_orders} bags</span></OverlayTrigger>
                                        </td>
                                    </tr>
                                    <tr style={{color: '#eeeeee'}}>
                                        <td><OverlayTrigger trigger={['hover', 'focus']} placement="left"
                                                            overlay={clfTooltip}><span>Customer lifetime value:</span></OverlayTrigger>
                                        </td>
                                        <td><OverlayTrigger trigger={['hover', 'focus']} placement="left"
                                                            overlay={clfTooltip}><span>$ {cluster.mean_ratio_amount_time}</span></OverlayTrigger>
                                        </td>
                                    </tr>
                                    <tr style={{color: '#eeeeee'}}>
                                        <td><OverlayTrigger trigger={['hover', 'focus']} placement="left"
                                                            overlay={spendingTooltip}><span>Total spending:</span></OverlayTrigger>
                                        </td>
                                        <td><OverlayTrigger trigger={['hover', 'focus']} placement="left"
                                                            overlay={spendingTooltip}><span>$ {cluster.mean_total_spending}</span></OverlayTrigger>
                                        </td>
                                    </tr>
                                    <tr style={{color: '#eeeeee'}}>
                                        <td><OverlayTrigger trigger={['hover', 'focus']} placement="left"
                                                            overlay={vouchersTooltip}><span>Vouchers used:</span></OverlayTrigger>
                                        </td>
                                        <td><OverlayTrigger trigger={['hover', 'focus']} placement="left"
                                                            overlay={vouchersTooltip}><span> {cluster.mean_vouchers_used}
                                            vouchers</span></OverlayTrigger></td>
                                    </tr>
                                    </tbody>
                                </table>
                            </div>

                        </div>
                    )

                });
            }

            return (
                <div className="container">


                    <div className="row">
                        <div className="col-xs-10 col-xs-offset-1 col-sm-6 col-sm-offset-3">
                            <h1 className="text-center">Customer Segments</h1>
                            {/*<h4 className="text-center">History and Forecast</h4>*/}
                            <br/>
                        </div>
                    </div>
                    <div className="row">
                        <div className="col-xs-offset-8 col-xs-4">
                            <label>Size by:</label>
                            <select className="form-control" value={this.state.size} onChange={this.handleChangeSize}>
                                <option value="size">Number of customers</option>
                                <option value="mean_interval">Average days between orders</option>
                                <option value="mean_one_off_orders">Mean One off orders</option>
                                <option value="mean_orders">Mean # of orders</option>
                                <option value="mean_ratio_amount_time">Mean ratio of amount spent against time</option>
                                <option value="mean_total_spending">Mean total spending</option>
                                <option value="mean_vouchers_used">Mean # of vouchers used</option>
                            </select>
                        </div>
                    </div>
                    <br/>
                    <div className="row">
                        <div className="col-xs-12 col-md-12">
                            <div id="viz" style={{boxSizing: 'content-box', height: '80%'}}></div>
                        </div>
                    </div>
                    <hr/>

                    <div className="row">
                        <h2>Segment Breakdown:</h2>
                        {clustersTableHtml ? clustersTableHtml : null}
                    </div>
                    <br/>
                </div>
            )
                ;
        }
    })
    ;


module.exports = withRouter(CustomerSegmentationPage);
