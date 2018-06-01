import React, { Component } from 'react';
import PropTypes from 'prop-types';
import {
  Modal,
  Button,
  Row,
  Col,
} from 'react-bootstrap';
import Select from 'react-select';
import 'react-select/dist/react-select.css';
import swal from 'sweetalert';
import 'sweetalert/dist/sweetalert.css';

import { ApiRequest } from '../../utils';


export default class OutOfCoffeeModal extends Component {

  static propTypes = {
    show: PropTypes.bool.isRequired,
    onHide: PropTypes.func.isRequired,
    onCoffeeSwitched: PropTypes.func.isRequired,
  }

  state = {
    coffeesFrom: [],
    coffeesTo: [],
    coffeeFrom: 0,
    coffeeTo: 0,
  }

  // componentDidMount() {
  //   this.getAllCoffees();
  //   this.getAvailableCoffees();
  // }

  componentWillReceiveProps(nextProps) {
    if (nextProps.show) {
      this.getAllCoffees();
      this.getAvailableCoffees();
    }
  }

  getAllCoffees = () => {
    ApiRequest.get('getAllCoffees/')
      .then(resp => (this.setState({ coffeesFrom: resp.data.coffees })))
      .catch(err => swal({ title: err, type: 'error' }));
  }

  getAvailableCoffees = () => {
    ApiRequest.get('getAvailableCoffees/')
      .then(resp => (this.setState({ coffeesTo: resp.data.coffees })))
      .catch(err => swal({ title: err, type: 'error' }));
  }

  handleInputChange = (name, obj) => {
    this.setState({ [name]: obj });
  }

  submitOutOfCoffee = (e) => {
    e.preventDefault();
    swal(
      {
        title: 'CAUTION!',
        text: 'Are you sure you want to proceed? This will affect ALL pending orders!',
        type: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#DD6B55',
        confirmButtonText: 'Yes, change all coffees!',
        closeOnConfirm: false,
      },
      confirm => (confirm ? this.switchCoffeeHandler() : null),
    );
  }

  switchCoffeeHandler = () => {
    const data = {
      coffee_from: this.state.coffeeFrom.value,
      coffee_to: this.state.coffeeTo.value,
    };
    ApiRequest.post('commands/switchCoffee', data)
      .then((resp) => {
        swal({
          title: 'Done!',
          text: resp.data.message,
          type: 'success',
          confirmButtonColor: '#DAA62A',
        });
        this.props.onCoffeeSwitched();
      })
      .catch((err) => {
        swal(err.message, err.response.data.error, 'error');
        this.props.onCoffeeSwitched();
      });
  };

  render() {
    const coffeesFrom = this.state.coffeesFrom.map(coffee => ({
      value: coffee.coffee_id,
      label: coffee.coffee_name,
    }));
    const coffeesTo = this.state.coffeesTo.map(coffee => ({
      value: coffee.coffee_id,
      label: coffee.coffee_name,
    }));

    return (
      <Modal
        show={this.props.show}
        onHide={this.props.onHide}
        className="text-center"
      >
        <Modal.Header closeButton>
          <Modal.Title componentClass="h3">Manage Your Coffee</Modal.Title>
        </Modal.Header>
        <form onSubmit={this.submitOutOfCoffee}>
          <Modal.Body>
            <Row>
              <Col xs={6}>Running Out Of:</Col>
              <Col xs={6}>Switch Coffee To:</Col>
            </Row>
            <hr />
            <Row>
              <Col xs={6}>
                <Select
                  name="coffeeFrom"
                  value={this.state.coffeeFrom}
                  options={coffeesFrom}
                  onChange={val => this.handleInputChange('coffeeFrom', val)}
                  clearable={false}
                  placeholder="Select a coffee"
                />
              </Col>
              <Col xs={6}>
                <Select
                  name="coffeeTo"
                  value={this.state.coffeeTo}
                  options={coffeesTo}
                  onChange={val => this.handleInputChange('coffeeTo', val)}
                  clearable={false}
                  placeholder="Select a coffee"
                />
              </Col>
            </Row>
          </Modal.Body>
          <Modal.Footer className="center-block">
            <Button type="submit">Confirm switching</Button>
          </Modal.Footer>
        </form>
      </Modal>
    );
  }
}
