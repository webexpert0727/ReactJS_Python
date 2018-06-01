import React, { Component } from 'react';
import PropTypes from 'prop-types';
import {
  Button,
  Form,
  FormGroup,
  FormControl,
  ControlLabel,
  InputGroup,
} from 'react-bootstrap';


export default class ScannerOrderField extends Component {

  static propTypes = {
    onSubmit: PropTypes.func.isRequired,
  }

  // componentDidMount() {
  //   this.orderID.focus();
  // }

  handleSubmit = (e) => {
    e.preventDefault();
    this.props.onSubmit(this.orderID.value);
    this.orderID.value = '';
    this.orderID.focus();
  }

  render() {
    return (
      <Form inline onSubmit={this.handleSubmit}>
        <FormGroup controlId="orderID">
          <ControlLabel>Enter the barcode for order processing:</ControlLabel>
          {' '}
          <InputGroup>
            <FormControl type="text" inputRef={v => (this.orderID = v)} autoFocus placeholder="@12345" />
            <InputGroup.Button>
              <Button type="submit" bsStyle="primary">
                <i className="fa fa-cogs" /> Process
              </Button>
            </InputGroup.Button>
          </InputGroup>
        </FormGroup>
      </Form>
    );
  }
}
