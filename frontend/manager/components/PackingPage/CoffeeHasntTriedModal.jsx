import React, { Component } from 'react';
import PropTypes from 'prop-types';
import {
  Modal,
  Table,
  Panel,
  Radio,
  Grid,
  Row,
  Col,
} from 'react-bootstrap';

import moment from 'moment';
import swal from 'sweetalert';
import 'sweetalert/dist/sweetalert.css';

import { ApiRequest, formatPackaging, formatStatus } from '../../utils';
import { OrderType } from '../../constants';
import styles from './PackingPage.css';


export default class CoffeeHasntTriedModal extends Component {

  static propTypes = {
    show: PropTypes.bool.isRequired,
    onHide: PropTypes.func.isRequired,
    orderID: PropTypes.number.isRequired,
    orderType: PropTypes.string.isRequired,
  }

  constructor(props) {
    super(props);
    this.data = {
      gift: null,
      referredBy: null,
      orderHistory: [],
      coffeesHasntTried: [],
      coffeesSampled: [],
    };
  }

  state = {
    loading: false,
  }

  componentWillReceiveProps(nextProps) {
    if (this.props.show === false &&
        nextProps.show === true &&
        this.isAllowedOrderType(nextProps.orderType)) {
      this.setState({ loading: true }, () => this.getCoffeeItems(nextProps.orderID));
    } else if (nextProps.show === false && typeof this.coffeeSampledID !== 'undefined') {
      this.updateCoffeesSampled();  // When the modal was hidden
    }
  }

  shouldComponentUpdate = nextProps => this.isAllowedOrderType(nextProps.orderType);

  getCoffeeItems(orderID) {
    // looks like a shit, I know
    ApiRequest.get(`coffeeModalItems/${orderID}?orderType=${this.props.orderType}`)
      .then((resp) => {
        this.data = resp.data;
        this.setState({ loading: false });
      })
      .catch(err => swal({ title: err, type: 'error' }));
  }

  isAllowedOrderType(orderType) {
    if (orderType === OrderType.REDEM) {
      return false;
    }
    return true;
  }

  updateCoffeesSampled() {
    const orderID = this.props.orderID;
    const coffeeSampledID = this.coffeeSampledID;
    delete this.coffeeSampledID; // reset for next order
    ApiRequest.post(`coffeesSampled/${orderID}`, { coffeeSampledID })
      .catch(err => swal({ title: err, type: 'error' }));
  }

  render() {
    const gifts = this.data.gifts
                 ? `Don't forget the gift! ${this.data.gifts}`
                 : 'No gift in this order.';

    const referredBy = this.data.referredBy
                       ? `This order was referred by ${this.data.referredBy}`
                       : 'No referral in this order.';

    const coffeesSampled = this.data.coffeesSampled;
    const coffeesHasntTried = this.data.coffeesHasntTried.map((coffee) => {
      const disabled = coffeesSampled.includes(coffee.name);
      return (
        <tr key={coffee.id}>
          <td>
            <Radio
              name="coffeeSampledID"
              value={coffee.id}
              className={disabled ? styles.coffeeSampleDisabled : ''}
              onChange={e => (this.coffeeSampledID = e.target.value)}
              disabled={disabled}
            >
              {coffee.name}
            </Radio>
          </td>
        </tr>);
    });

    const orderHistory = this.data.orderHistory.map((order, i) => (
      <tr key={order.id}>
        <td>{i + 1}</td>
        <td>{order.coffee}</td>
        <td>{formatPackaging(order.packaging_method)}</td>
        <td>{order.brew_method}</td>
        <td>{moment(order.created_date * 1000).format('MMMM DD, YYYY')}</td>
        <td>{moment(order.shipping_date * 1000).format('MMMM DD, YYYY')}</td>
        <td>{formatStatus(order.status)}</td>
      </tr>
    ));

    const loading = <i className="fa fa-spinner fa-spin fa-3x" />;

    return (
      <Modal show={this.props.show} onHide={this.props.onHide} className="text-center" dialogClassName="modal-dialog-wide">
        <Modal.Body>

          <Grid>
            <Row>
              <Col md={6}>
                <Panel header="Order details" bsStyle="warning">
                  { this.state.loading ? loading : <div> {gifts} <br /> {referredBy} </div> }
                </Panel>
                <Panel header="Coffees which the customer hasn't tried before" bsStyle="info">
                  <Table condensed hover fill>
                    <tbody>
                      { this.state.loading
                        ? <tr><td className={styles.loading}>{loading}</td></tr>
                        : coffeesHasntTried }
                    </tbody>
                  </Table>
                </Panel>
              </Col>

              <Col md={6}>
                <Panel header="Customer Order History" bsStyle="success">
                  <Table condensed hover fill>
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Coffee</th>
                        <th>Brew Method</th>
                        <th>Packaging method</th>
                        <th>Created</th>
                        <th>Shipping date</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      { this.state.loading
                        ? <tr><td className={styles.loading} colSpan={7}>{loading}</td></tr>
                        : orderHistory }
                    </tbody>
                  </Table>
                </Panel>
              </Col>

            </Row>
          </Grid>

        </Modal.Body>

        <Modal.Footer>
          Please press escape on keyboard to close this modal window
        </Modal.Footer>
      </Modal>
    );
  }
}
