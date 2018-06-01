import React, { Component } from 'react';
import ReactCSSTransitionGroup from 'react-addons-css-transition-group';
import {
  Button,
  Checkbox,
  Grid,
  Row,
  FormGroup,
  FormControl,
  InputGroup,
  Col,
  Nav,
  NavItem,
  ButtonToolbar,
} from 'react-bootstrap';

import $ from 'jquery';
import moment from 'moment';
import 'bootstrap';
import 'datatables.net-bs';
import 'datatables.net-bs/css/dataTables.bootstrap.css';
import swal from 'sweetalert';
import 'sweetalert/dist/sweetalert.css';
import 'bootstrap-daterangepicker';
import 'bootstrap-daterangepicker/daterangepicker.css';

import { ApiRequest, printPDF, downloadPDF } from '../../utils';
import { OrderType } from '../../constants';
import styles from './PackingPage.css';

import StickerModal from './StickerModal';
import OutOfCoffeeModal from './OutOfCoffeeModal';
import CoffeeHasntTriedModal from './CoffeeHasntTriedModal';
import ScannerOrderField from './ScannerOrderField';
import OrdersTable from './OrdersTable';


const log = console.log;


class OrderUtils {

  static isGearOrder(orderID) {
    return /G/.test(orderID);
  }

  static isRedemOrder(orderID) {
    return /R/.test(orderID);
  }

  static cleanOrderID(orderID) {
    // .../qr-social/@600/  || @600/ => 600, false
    // .../qr-social/@G600/ || G600 => 600, true
    const matches = /(@[GR]?\d+)/.exec(orderID);
    if (!matches) {
      return NaN;
    }
    return parseInt(matches[1].replace(/@[GR]?/, ''), 10);
  }

  static handleOrderRemarks(orders) {
    return orders.map((_order) => {
      const order = _order;
      const remarks = order.remarks;
      const remarksKeys = Object.keys(remarks);
      if (remarksKeys.length > 0) {
        order.remarksPrint = remarksKeys
          .reduce((str, key) => `${str} ${key}: ${remarks[key]},`, '')
          .slice(0, -1)
          .replace('_', ' ')
          .replace(': true', '');
      }
      if (order.gift) {
        order.remarksPrint = order.remarksPrint || '';
        if (!order.remarksPrint.includes(order.gift)) {
          order.remarksPrint += `GIFT: ${order.gift}`;
        }
      }
      return order;
    });
  }

  static orderProcessSuccessful(orderID, resp) {
    let remarks = '';
    for (let order in this.state.orders) {
      if (this.state.orders[order]['id'] == orderID) {
        remarks = this.state.orders[order]['gift'];
      }
    }
    if (remarks) {
      swal({
        title: 'Gift for this order found!',
        text: `Do not forget to pack the
               ${JSON.stringify(remarks, null, 4)}`,
        type: 'warning',
        confirmButtonColor: '#F55449',
        confirmButtonText: "Yes, I'm aware",
        closeOnConfirm: false,
      })
    }
    printPDF($('#pdfdoc'), resp);
    this.removeOrder(orderID);
  }

  static orderProcessFailed(orderID, err) {
    log('orderProcessFailed!', err);
    if (err.response.status === 402) {
      swal({
        title: 'Stop Packing! Payment declined!',
        text: `Insufficient funds in credit card!
               ${err.response.data.error}`,
        type: 'warning',
        confirmButtonColor: '#F55449',
        confirmButtonText: "Yes, I'm aware",
        closeOnConfirm: false,
      }, () => swal({
        title: 'Moved!',
        text: "Order has been moved 'Declined' tab",
        type: 'success',
        confirmButtonColor: '#DAA62A',
      }));

      this.removeOrder(orderID);
    } else {
      swal({
        title: 'Error with processing the order',
        text: err.response.data.error,
        type: 'error',
      });
    }
  }
}


export default class PackingPage extends Component {

  constructor(props) {
    super(props);
    this.backlog = null;
    this.brewMethods = [];
    this.currentRequest = '';
    this.coffeeFrom = null;
    this.coffeeTo = null;
    this.to_be_shipped_today_count = 0;
    this.backlog_count = 0;
  }

  state = {
    startDate: moment(),
    orders: [],
    filter: [],
    processedOrders: [],
    brewMethod: [
      'Aeropress', 'Drip', 'Espresso', 'French press',
      'Cold Brew', 'Stove top', 'None'],
    loading: false,
    activeTab: 'packaging',
    currentProcessOrderID: -1,
    currentProcessOrderType: '',
    currentPrintOrderID: -1,
    currentPrintOrderType: '',
    showStickerModal: false,
    showOutOfCoffeeModal: false,
    showCoffeeHasntTriedModal: false,
  }

  componentDidMount() {
    this.getBrewMethods();
    this.getOrders();
    $('#startdate').daterangepicker(
      {
        locale: {
          format: 'DD/MM/YYYY',
        },
        singleDatePicker: true,
        autoApply: true,
      },
      (start) => {
        this.setState({ startDate: moment(start, 'DD/MM/YYYY') });
        this.getOrders();
      },
    );
  }

  getBrewMethods() {
    ApiRequest.get('brewMethods')
      .then(resp => (this.brewMethods = resp.data))
      .catch(err => log(err));
      // .catch(err => swal({ title: err, type: 'error' }));
  }

  getToBeShippedCount() {
    const startDate = this.state.startDate.format('DD-MM-YYYY');
    const data = {
      date: startDate,
      backlog: this.backlog.checked,
    };
    ApiRequest.post('toBeShippedCount', data)
      .then(resp => {
        log(resp);
        this.to_be_shipped_today_count = resp.data.orders;
        this.backlog_count = resp.data.backlog;
      })
      .catch(err => log(err));
  }

  getOrders = (brewMethod, filter) => {
    log(`getOrders: brew: ${brewMethod}, filter: ${filter}`);
    this.setState({ loading: true });
    this.getToBeShippedCount();
    if (this.currentRequestTokenSource) {
      this.currentRequestTokenSource.cancel();
    }
    const startDate = this.state.startDate.format('DD-MM-YYYY');
    const data = {
      date: startDate,
      backlog: this.backlog.checked,
      brew_method: typeof brewMethod === 'undefined' ? this.state.brewMethod : brewMethod,
    };
    if (startDate === 'Invalid date') {
      this.setState({ orders: [] });
      return;
    }

    let url;
    const currentFilter = filter || this.state.activeTab;
    log('filter, state.activeTab:', filter, this.state.activeTab);
    if (currentFilter === 'packaging' ||
        currentFilter === 'nespresso') url = 'packingOrders';
    else if (currentFilter === 'bottled') url = 'bottledOrders';
    else if (currentFilter === 'gears') url = 'gearOrders';
    else if (currentFilter === 'christmas') url = 'christmasOrders';
    else if (currentFilter === 'declined') url = 'declinedOrders';
    else if (currentFilter === 'tasterpack') url = 'tasterPackOrders';
    else if (currentFilter === 'multipleOrders') url = 'multipleOrders';
    else if (currentFilter === 'freebies') url = 'unredeemedItems';
    else if (currentFilter === 'worldwideCoffee') url = 'worldWideCoffeeOrders';
    else if (currentFilter === 'worldwideGear') url = 'worldWideGearOrders';

    this.currentRequestTokenSource = ApiRequest.getCancelTokenSource();
    const cancelToken = this.currentRequestTokenSource.token;

    ApiRequest.post(url, data, { cancelToken })
      .then((resp) => {
        const orders = OrderUtils.handleOrderRemarks(resp.data.orders || []);
        this.setState({ orders, loading: false, brewMethod: data.brew_method });
      })
      .catch(err => swal(err.message, err.response.data.error, 'error'));
  }

  setTab = (tab) => {
    if (tab === 'packaging') {
      const brewMethod = ['Aeropress', 'Drip', 'Espresso', 'French press', 'Stove top', 'Cold Brew', 'None'];
      this.setState({ brewMethod, activeTab: tab }, () => this.getOrders(brewMethod, tab));
    } else if (tab === 'nespresso') {
      const brewMethod = ['Nespresso'];
      this.setState({ brewMethod, activeTab: tab }, () => this.getOrders(brewMethod, tab));
    } else {
      this.setState({ activeTab: tab }, () => this.getOrders(null, tab));
    }
  }

  printLabels = () => {
    const orders = this.state.orders.map(order => [order.id, order.type]);
    ApiRequest.post('orderLabels', { orders }, { responseType: 'blob' })
      .then(resp => downloadPDF(resp))
      .catch(err => log(err));
  }

  printAddresses = () => {
    const orders = this.state.orders.map(order => [order.id, order.type]);
    ApiRequest.post('orderAddresses', { orders }, { responseType: 'blob' })
      .then(resp => downloadPDF(resp))
      .catch(err => log(err));
  }

  printPostcards = () => {
    const orders = this.state.orders.map(order => [order.id, order.type]);
    ApiRequest.post('orderPostcards', { orders }, { responseType: 'blob' })
      .then(resp => downloadPDF(resp))
      .catch(err => log(err));
  }

  toggleOutOfCoffeeModal = () => {
    this.setState({ showOutOfCoffeeModal: !this.state.showOutOfCoffeeModal });
  }

  toggleStickerModal = (orderID, orderType) => {
    this.setState({
      currentPrintOrderID: parseInt(orderID, 10),
      currentPrintOrderType: orderType,
      showStickerModal: !this.state.showStickerModal,
    });
  }

  toggleCoffeeHasntTriedModal = () => {
    this.setState({
      showCoffeeHasntTriedModal: !this.state.showCoffeeHasntTriedModal,
    });
  }

  checkOnMultipleOrders = () => {
    const { currentProcessOrderID: orderID,
            currentProcessOrderType: orderType,
            startDate } = this.state;
    const data = {
      date: startDate.format('DD-MM-YYYY'),
      backlog: this.backlog.checked,
      orderType,
    };
    ApiRequest.post(`customerHasMultipleOrders/${orderID}`, data)
      .then((resp) => {
        if (resp.data.has_multiple_orders === true) {
          swal({
            title: 'Customer has more then one order!',
            text: 'Hold this one side and compile it with other orders.',
            type: 'warning',
            confirmButtonColor: '#DAA62A',
            confirmButtonText: "Yes, I'm aware",
          });
        }
      })
      .catch(err => log(err));
  }

  toggleProcessingModals = () => {
    this.toggleCoffeeHasntTriedModal();
    this.checkOnMultipleOrders();
  }

  processOrder = (_orderID) => {
    const isGear = OrderUtils.isGearOrder(_orderID);
    const isRedem = OrderUtils.isRedemOrder(_orderID);
    const orderID = OrderUtils.cleanOrderID(_orderID);
    let orderType;
    if (isGear) {
      orderType = OrderType.GEAR;
    } else if (isRedem) {
      orderType = OrderType.REDEM;
    } else {
      orderType = OrderType.COFFEE;
    }
    log(`processOrder: [${_orderID}] => ${orderID}; type: ${orderType}`);

    if (isNaN(orderID)) {
      swal({ title: `orderID: ${_orderID} => ${orderID}`, type: 'error' });
      return;
    } else if (this.state.processedOrders.includes(orderID)) {
      swal({
        title: 'Error with processing the order',
        text: `[${orderID}] Order has already been or is currently being processed!`,
        type: 'error',
      });
      return;
    }

    this.state.processedOrders.push(orderID);
    this.setState({
      currentProcessOrderID: orderID,
      currentProcessOrderType: orderType,
    }, this.toggleProcessingModals);

    ApiRequest.post(`commands/processOrder/${orderID}`, { orderType }, { responseType: 'blob' })
      .then(OrderUtils.orderProcessSuccessful.bind(this, orderID))
      .catch(OrderUtils.orderProcessFailed.bind(this, orderID));
  }

  removeOrder(orderID) {
    const orders = this.state.orders.filter(order => order.id !== orderID);
    this.setState({ orders });
  }

  render() {
    const activeTab = this.state.activeTab;

    return (
      <ReactCSSTransitionGroup
        transitionAppear
        transitionName="fade"
        transitionAppearTimeout={400}
        transitionEnterTimeout={400}
        transitionLeaveTimeout={400}
      >

        <OutOfCoffeeModal
          show={this.state.showOutOfCoffeeModal}
          onHide={this.toggleOutOfCoffeeModal}
          onCoffeeSwitched={() => {
            this.getOrders();
            this.toggleOutOfCoffeeModal();
          }}
        />

        <StickerModal
          show={this.state.showStickerModal}
          onHide={this.toggleStickerModal}
          orderID={this.state.currentPrintOrderID}
          orderType={this.state.currentPrintOrderType}
        />

        <CoffeeHasntTriedModal
          show={this.state.showCoffeeHasntTriedModal}
          onHide={this.toggleCoffeeHasntTriedModal}
          orderID={this.state.currentProcessOrderID}
          orderType={this.state.currentProcessOrderType}
        />

        <Grid fluid>

          <Row>
            <h1 className={styles.title}>{this.to_be_shipped_today_count} orders to be Shipped Today</h1>
          </Row>

          <Row className={styles.datePicker}>
            <Col xs={12} md={4} mdOffset={4}>
              <FormGroup>
                <InputGroup bsSize="lg">
                  <FormControl type="text" id="startdate" />
                  <InputGroup.Addon>
                    <i className="fa fa-calendar" />
                  </InputGroup.Addon>
                </InputGroup>
              </FormGroup>
              <FormGroup>
                <Checkbox
                  inputRef={r => (this.backlog = r)}
                  onChange={() => this.getOrders()}
                  defaultChecked
                >
                  Include Backlogs ({this.backlog_count})
                </Checkbox>
              </FormGroup>
            </Col>
          </Row>

          <Row>
            <Col xs={12}>
              <ScannerOrderField onSubmit={this.processOrder} ref={r => (this.scanField = r)} />
            </Col>
          </Row>

          <Row>
            <span id="pdfdoc" />
          </Row>

          <Row>
            <Col xs={12}>
              <Nav bsStyle="tabs" activeKey={activeTab} onSelect={this.setTab} className={styles.tabs}>
                <NavItem eventKey="packaging">Packaging</NavItem>
                <NavItem eventKey="nespresso">Shotpods</NavItem>
                <NavItem eventKey="bottled">Bottled</NavItem>
                <NavItem eventKey="tasterpack">Taster Pack</NavItem>
                <NavItem eventKey="gears">Gears</NavItem>
                <NavItem eventKey="christmas">Christmas</NavItem>
                <NavItem eventKey="freebies">Freebies</NavItem>
                <NavItem eventKey="multipleOrders">Multiple</NavItem>
                <NavItem eventKey="declined">Declined</NavItem>
                <NavItem eventKey="worldwideCoffee">WorldWide Bags</NavItem>
                <NavItem eventKey="worldwideGear">WorldWide Gears</NavItem>
              </Nav>
            </Col>
          </Row>

          <Row>
            <Col xs={12}>
              <ButtonToolbar className={styles.btnToolbar}>
                <Button bsStyle="primary" bsSize="small" onClick={this.printLabels}>
                  <i className="fa fa-tag" /> Print Labels
                </Button>
                <Button bsStyle="primary" bsSize="small" onClick={this.printAddresses}>
                  <i className="fa fa-map" /> Print Addresses
                </Button>
                <Button bsStyle="primary" bsSize="small" onClick={this.printPostcards}>
                  <i className="fa fa-newspaper-o" /> Print Postcards
                </Button>
                <Button bsStyle="primary" bsSize="small" onClick={this.toggleOutOfCoffeeModal}>
                  <i className="fa fa-exclamation-triangle" /> Running Out of Orders
                </Button>
              </ButtonToolbar>
            </Col>
          </Row>

          <Row>
            <Col xs={12}>
              { this.state.loading
                ? <div className={styles.loadingOrders}><i className="fa fa-spinner fa-spin fa-3x" /></div>
                : <OrdersTable
                  orders={this.state.orders}
                  processOrder={this.processOrder}
                  toggleStickerModal={this.toggleStickerModal}
                />
              }
            </Col>
          </Row>

        </Grid>

      </ReactCSSTransitionGroup>
    );
  }
}
