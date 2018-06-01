import React, { Component } from 'react';
import PropTypes from 'prop-types';
import {
  Modal,
  Button,
  Checkbox,
} from 'react-bootstrap';

import $ from 'jquery';
import swal from 'sweetalert';
import 'sweetalert/dist/sweetalert.css';

import { ApiRequest, printPDF, downloadPDF } from '../../utils';


export default class StickerModal extends Component {

  static propTypes = {
    show: PropTypes.bool.isRequired,
    onHide: PropTypes.func.isRequired,
    orderID: PropTypes.number.isRequired,
    orderType: PropTypes.string.isRequired,
  }

  handlePrint = (e) => {
    e.preventDefault();
    const { orderID, orderType } = this.props;
    const orders = [[orderID, orderType]];
    if (this.label.checked) {
      ApiRequest.post('orderLabels', { orders }, { responseType: 'blob' })
        .then(resp => downloadPDF(resp))
        .catch(err => swal({ title: err, type: 'error' }));
    }
    if (this.address.checked) {
      ApiRequest.post('orderAddresses', { orders }, { responseType: 'blob' })
        .then(resp => printPDF($('#pdfdoc'), resp))
        .catch(err => swal({ title: err, type: 'error' }));
    }
  }

  render() {
    return (
      <Modal show={this.props.show} onHide={this.props.onHide}>
        <Modal.Header closeButton>
          <Modal.Title componentClass="h3">Print only for this order</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <form onSubmit={this.handlePrint}>
            <Checkbox inputRef={v => (this.label = v)} defaultChecked>Print Label</Checkbox>
            <Checkbox inputRef={v => (this.address = v)} defaultChecked>Print Address</Checkbox>
            <Button type="submit">Send To Printer</Button>
          </form>
        </Modal.Body>
      </Modal>
    );
  }
}
