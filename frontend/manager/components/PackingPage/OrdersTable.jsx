import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { Table, Button } from 'react-bootstrap';
// import cx from 'classnames';

import $ from 'jquery';
import moment from 'moment';
import 'datatables.net-bs';
import 'datatables.net-bs/css/dataTables.bootstrap.css';

import { formatPackaging, formatStatus } from '../../utils';
import { OrderType } from '../../constants';
import styles from './PackingPage.css';


const dataTableConfig = {
  aaSorting: [],
  aoColumnDefs: [
    {
      bSortable: false,
      aTargets: [0, 9],
    },
    {
      bSearchable: false,
      aTargets: [9],
    },
  ],
  bDestroy: true,
};


export default class OrdersTable extends Component {

  static propTypes = {
    orders: PropTypes.arrayOf(PropTypes.object).isRequired,
    processOrder: PropTypes.func.isRequired,
    toggleStickerModal: PropTypes.func.isRequired,
  }

  componentDidMount() {
    $('#data-table').DataTable(dataTableConfig);
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.orders.length !== this.props.orders.length) {
      $('#data-table').DataTable().destroy();
    }
  }

  componentDidUpdate() {
    $('#data-table').DataTable(dataTableConfig);
  }

  processOrder = e => this.props.processOrder(e.currentTarget.dataset.orderId)

  toggleStickerModal = (e) => {
    const { orderId, orderType } = e.currentTarget.dataset;
    return this.props.toggleStickerModal(orderId, orderType);
  }

  handleOrders = () => this.props.orders.map((order, i) => {
    let prefix = '';
    if (order.type === OrderType.GEAR) prefix = 'G';
    else if (order.type === OrderType.REDEM) prefix = 'R';

    return (
      <tr key={order.id}>
        <td>{i + 1}</td>
        <td>{order.name}</td>
        <td>{order.email}</td>
        <td>{order.coffee}</td>
        <td>{order.brew_method}</td>
        <td>{formatPackaging(order.packaging_method)}</td>
        <td>{moment(order.created_date * 1000).format('MMMM DD, YYYY')}</td>
        <td>{moment(order.shipping_date * 1000).format('MMMM DD, YYYY')}</td>
        <td>{formatStatus(order.status)}</td>
        <td>
          <Button
            bsStyle="primary" bsSize="xsmall"
            data-order-id={`@${prefix}${order.id}`}
            onClick={this.processOrder}
          >
            Process
          </Button>
        </td>
        <td>{order.remarksPrint ? order.remarksPrint : ''}</td>
        <td>
          <Button data-order-type={order.type} data-order-id={order.id} onClick={this.toggleStickerModal}>
            <i className="fa fa-print" />
          </Button>
        </td>
      </tr>);
  });

  render() {
    const orders = this.handleOrders();

    if (this.props.orders.length === 0) {
      return <h3 className={styles.noHaveOrders}>- No orders -</h3>;
    }

    return (
      <div className={styles.tableWrapper}>
        <Table id="data-table" condensed hover>
          <thead>
            <tr>
              <th>#</th>
              <th>Name</th>
              <th>Email</th>
              <th>Coffee</th>
              <th>Brew Method</th>
              <th>Packaging</th>
              <th>Created</th>
              <th>Shipping Date</th>
              <th>Status</th>
              <th>Checkout</th>
              <th>Remarks</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {orders}
          </tbody>
          <tfoot />
        </Table>
      </div>
    );
  }
}
