import React, { Component } from 'react';
import PropTypes from 'prop-types';
import ReactDOM from 'react-dom';
import DatePicker from 'react-datepicker';
import moment from 'moment';
import axios from 'axios';

import 'react-datepicker/dist/react-datepicker.css';
import './ShoppingCart.css';

class MenuItem extends React.Component {
  render() {
    return (
      <a className="dropdown-toggle" role="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
        {/* <span className="glyphicon glyphicon-shopping-cart" /> */}
        <img width="20" height="20" src="/static/images/icons/nav/shopcart.png" />&nbsp;
        (<span>{ this.props.count }</span> items)
      </a>
    );
  }
}
MenuItem.propTypes = {
  count: React.PropTypes.number,
};
MenuItem.defaultProps = {
  count: 0,
};

class Tooltip1 extends Component {
  render() {
    return (
      <span className="glyphicon glyphicon-info-sign pull-right" aria-hidden="true"
          data-toggle="tooltip" data-placement="left"
          title="We will send the order to your registered address on your account">
      </span>
    );
  }
}

class Coffee extends Component {
  render() {
    return (
      <div className="prod-name">
        <p><b>{this.props.coffee ? this.props.coffee.name : this.props.gear.name}</b></p>
        <a onClick={this.props.onDelete}>
          <span className="glyphicon glyphicon-trash" aria-hidden="true" />
        </a>
      </div>
    );
  }
}

class Quantity extends Component {
  render() {
    return (
      <div className="prod-info">
        <p>
          {this.props.coffee ? (this.props.coffee.brew == 'None' ? "" : this.props.coffee.brew) : ('Gear') }
          &nbsp;
          {this.props.coffee ? (this.props.coffee.name == "Discovery Programme" ? package_mapper_discovery[this.props.coffee.package] : package_mapper[this.props.coffee.package]) : '' }
        </p>

        <div className="prod-item">
          <div className="prod-qty">
            <a className="btn btn-primary-inv" onClick={this.props.onDecrease}>
              <span className="glyphicon glyphicon-minus" aria-hidden="true"/>
            </a>

            <span className="s-h1-bold">{this.props.quantity}</span>

            <a className="btn btn-primary-inv" onClick={this.props.onIncrease}>
              <span className="glyphicon glyphicon-plus" aria-hidden="true" />
            </a>
          </div>

          <p className="prod-price">S${this.props.coffee ? this.props.coffee.price * this.props.quantity : this.props.gear.price * this.props.quantity }</p>
        </div>

      </div>
    );
  }
}

class Summary extends Component {
  render() {
    return (
      <div className="cart-header">
        <p className="s-h1-bold">My Shopcart</p>
        <p>Total:&nbsp;S${this.props.total}</p>
      </div>
    );
  }
}

class Order extends React.Component {
  constructor(props) {
    super(props);
    this.onDecrease = this.onDecrease.bind(this);
    this.onIncrease = this.onIncrease.bind(this);
    this.onDelete = this.onDelete.bind(this);
  }
  onDecrease() {
    this.props.onDecrease(this);
  }
  onIncrease() {
    console.log("Increase!");
    this.props.onIncrease(this);
  }
  onDelete() {
    this.props.onDelete(this);
  }
  render() {
    return (
      <li>
        <Coffee
          coffee={this.props.coffee ? this.props.coffee : this.props.gear }
          quantity={this.props.quantity}
          onDelete={this.onDelete}
        />
        <Quantity
          coffee={this.props.coffee ? this.props.coffee : this.props.gear }
          quantity={this.props.quantity}
          onDecrease={this.onDecrease}
          onIncrease={this.onIncrease}
        />
      </li>
    );
  }
}

class OrderList extends React.Component {
  render() {
    let items = [];
    this.props.items.forEach((item) => {
      let key;
      if (item.coffee) {
        key = `${item.coffee.name}-${item.coffee.brew}-${item.coffee.package}`;
      } else if (item.workshop) {
        key = `${item.workshop.name}`;
      } 
      else {
        key = `${item.gear.name}`;
      }
      items.push(
        <Order
          key={key}
          coffee={item.coffee || item.gear || item.workshop}
          quantity={item.quantity}
          onDecrease={this.props.onDecrease}
          onIncrease={this.props.onIncrease}
          onDelete={this.props.onDelete}
        />);
    });
    return (
      <ul className="cart-items">
        {items}
      </ul>
    );
  }
}

function CheckoutButton(props) {
  if (props.len > 0) {
    return (
      <a
        className="btn btn-primary btn-hc btn-hc-xs pull-right"
        href="/coffees/checkout"
      >
        Checkout
      </a>
    );
  } else {
    return <span />
  }
};

export default class ShoppingCart extends Component {
  // WARNING: experimental ES7 syntax spotted
  static propTypes = {
    // items: React.PropTypes.arrayOf(React.PropTypes.any).isRequired,
  }
  constructor(props) {
    super(props);

    this.delete = this.delete.bind(this);
    this.increase = this.increase.bind(this);

    axios.defaults.xsrfCookieName = 'csrftoken';
    axios.defaults.xsrfHeaderName = 'X-CSRFToken';

    this.state = {
      items: [],
      startDate: moment(),
      initialized: false,
    };
    this.handleChange = this.handleChange.bind(this);
  };
  handleChange = (newDate) => {
    console.log("newDate", newDate);
    return this.setState({startDate: newDate});
  };

  componentDidMount() {
    axios.post('/load-cart/')
    .then((response) => {
      this.setState({
        items: response.data,
      });
    })
    .catch((error) => {
      console.log(error);
    });
  }
  componentDidUpdate() {
    if (!this.state.initialized) {
      const btnsAddBagHtmlCollection = document.getElementsByClassName('btn-add-bag-placement');
      const btnsAddBagArray = [].slice.call(btnsAddBagHtmlCollection);
      btnsAddBagArray.forEach((btn) => {
        ReactDOM.render(
          <button
            className="btn btn-primary-white btn-hc btn-hc-xs"
            data-id={btn.getAttribute('data-id')}
            onClick={this.addBag}
          >Add to cart
          </button>,
          btn);
      });

      const btnsAddCourseHtmlCollection = document.getElementsByClassName('btn-add-course-placement');
      const btnsAddCourseArray = [].slice.call(btnsAddCourseHtmlCollection);
      btnsAddCourseArray.forEach((btn) => {
        ReactDOM.render(
          <button
            className="btn btn-primary-white btn-hc btn-hc-xs"
            data-id={btn.getAttribute('data-id')}
            onClick={this.addCourse}
          >Add to cart
          </button>,
          btn);
      });

      const btnsAddPodsHtmlCollection = document.getElementsByClassName('btn-add-pods-placement');
      const btnsAddPodsArray = [].slice.call(btnsAddPodsHtmlCollection);
      btnsAddPodsArray.forEach((btn) => {
        ReactDOM.render(
          <button
            className="btn btn-primary-white btn-hc btn-hc-xs"
            data-id={btn.getAttribute('data-id')}
            onClick={this.addPods}
          >Add to cart
          </button>,
          btn);
      });

      const btnsAddGearHtmlCollection = document.getElementsByClassName('btn-add-gear-placement');
      const btnsAddGearArray = [].slice.call(btnsAddGearHtmlCollection);
      btnsAddGearArray.forEach((btn) => {
        ReactDOM.render(
          <button
            className="btn btn-primary-white btn-hc btn-hc-xs"
            data-id={btn.getAttribute('data-id')}
            onClick={this.addGear}
          >Add to cart
          <Tooltip1 />
          </button>,
          btn);
      });

      const btnsAddBottledHtmlCollection = document.getElementsByClassName('btn-add-bottled-placement');
      const btnsAddBottledArray = [].slice.call(btnsAddBottledHtmlCollection);
      btnsAddBottledArray.forEach((btn) => {
        ReactDOM.render(
          <button
            className="btn btn-primary-white btn-hc btn-hc-xs"
            data-id={btn.getAttribute('data-id')}
            onClick={this.addBottled}
          >Add to cart
          </button>,
          btn);
      });

      const btnsPlusMinusHtmlCollection = document.getElementsByClassName('plus-minus');
      const btnsPlusMinusArray = [].slice.call(btnsPlusMinusHtmlCollection);
      btnsPlusMinusArray.forEach((btn) => {
        ReactDOM.render(
          <div className="plus-minus">
            <button
              className="btn btn-primary-white btn-hc btn-hc-xs"
              data-id={btn.getAttribute('data-id')}
              onClick={this.decrease0}
            >
              <span className="glyphicon glyphicon-minus" data-id={btn.getAttribute('data-id')} />
            </button>
            <p className="s-h1-bold">1</p>
            <button
              className="btn btn-primary-white btn-hc btn-hc-xs"
              data-id={btn.getAttribute('data-id')}
              onClick={this.increase0}
            >
              <span className="glyphicon glyphicon-plus" data-id={btn.getAttribute('data-id')} />
            </button>
          </div>,
          btn);
      });

      this.setState({
        initialized: true,
      });
    }
    const btnsAddDateHtmlCollection = 
    document.getElementsByClassName('workshop-date');
    const datesArray = [].slice.call(btnsAddDateHtmlCollection);
    datesArray.forEach((btn) => {
      ReactDOM.render(
       <div>
        <DatePicker selected={this.state.startDate}
                    onChange={this.handleChange} />
      </div>,
      btn);
    });
  }
  getQuantity() {
    let x = 0;
    this.state.items.forEach((item) => {
      x += item.quantity;
    });
    return x;
  }
  getSummary() {
    let x = 0;
    this.state.items.forEach((item) => {
    if (item.coffee){
        x += item.coffee.price * item.quantity;
    } else if(item.gear) {
        x += item.gear.price * item.quantity
      }
    else{
        x += item.workshop.price * item.quantity
      }
    });
    return x;
  }
  addBag = (event) => {
    const coffeeId = event.target.getAttribute('data-id');
    const data = {
      coffee_id: coffeeId,
      brew_id: document.getElementById(`pbox-oneoff-brewmethod__${coffeeId}`).getAttribute('data-brew-id'),
      package_id: document.getElementById(`pbox-oneoff-packaging__${coffeeId}`).getAttribute('data-package-id'),
      qty: document.getElementById(`pbox-oneoff-quantity__${coffeeId}`).getElementsByTagName('p')[0].innerHTML,
    };
    axios.post('/add-cart/', data)
    .then((response) => {
      let items = this.state.items;
      let needAddition = true;
      items.forEach((item) => {
        if (item.coffee) {
          if (response.data.name === item.coffee.name &&
            response.data.brew === item.coffee.brew &&
            response.data.package === item.coffee.package) {
            item.quantity += response.data.qty;
            needAddition = false;
            return;
          }
        }
      });
      const new_item = {
          coffee: {
              id: response.data.coffee_id,
              name: response.data.name,
              price: response.data.price,
              brew: response.data.brew,
              brew_id: response.data.brew_id,
              package: response.data.package
          },
          quantity: response.data.qty,
      }
      if (needAddition) {
        items.push(new_item, );
      }
      this.syncCart(items);

      fbq('track', "AddToCart", {
        value: response.data.price,
        currency: 'SGD',
        content_name: response.data.name,
        content_type: 'BAG',
        content_ids: [response.data.coffee_id, ],
        contents: new_item
      });
    })
    .catch((error) => {
      console.log(error);
    });
    // close coffee details modal (jQuery off!)
    document.querySelectorAll('.modal.in button.close')[0].click();
    document.querySelectorAll('#shopping-cart a')[0].click();
  }
  addCourse = (event) => {
    const courseId = event.target.getAttribute('data-id');
    const data = {
      course_id: courseId,
      qty: document.getElementById(`pbox-oneoff-quantity__${courseId}`).getElementsByTagName('p')[0].innerHTML,
      date: this.state.date,
    };
    axios.post('/add-cart/course/', data)
    .then((response) => {
      let items = this.state.items;
      let needAddition = true;
      items.forEach((item) => {
        if (item.workshop) {
          if (response.data.name === item.workshop.name) {
            item.quantity += response.data.qty;
            needAddition = false;
            return;
          }
        }
      });
      const new_item = {
          workshop: {
              id: response.data.course_id,
              name: response.data.name,
              price: response.data.price,
              date: this.state.startDate
          },
          quantity: response.data.qty,
      }
      if (needAddition) {
        items.push(new_item, );
      }
      this.syncCart(items);

      fbq('track', "AddToCart", {
        value: response.data.price,
        currency: 'SGD',
        content_name: response.data.name,
        content_type: 'COURSE',
        content_ids: [response.data.course_id, ],
        contents: new_item
      });
    })
    .catch((error) => {
      console.log(error);
    });
    // close coffee details modal (jQuery off!)
    document.querySelectorAll('.modal.in button.close')[0].click();
    document.querySelectorAll('#shopping-cart a')[0].click();
  }

  addPods = (event) => {
    const coffeeId = event.target.getAttribute('data-id');
    const data = {
      coffee_id: coffeeId,
      qty: document.getElementById(`pbox-oneoff-quantity__${coffeeId}`).getElementsByTagName('p')[0].innerHTML,
    };
    axios.post('/add-pods/', data)
    .then((response) => {
      let items = this.state.items;
      let needAddition = true;
      items.forEach((item) => {
        if (item.coffee) {
          if (response.data.name === item.coffee.name) {
            item.quantity += response.data.qty;
            needAddition = false;
            return;
          }
        }
      });
      const new_item = {
          coffee: {
              id: response.data.coffee_id,
              name: response.data.name,
              price: response.data.price,
              package: 'PODS',
              brew_id: response.data.brew_id,
          },
          quantity: response.data.qty,
      }
      if (needAddition) {
        items.push(new_item, );
      }
      this.syncCart(items);

      fbq('track', "AddToCart", {
        value: response.data.price,
        currency: 'SGD',
        content_name: response.data.name,
        content_type: 'PODS',
        content_ids: [response.data.coffee_id, ],
        contents: new_item
      });
    })
    .catch((error) => {
      console.log(error);
    });
    document.querySelectorAll('.modal.in button.close')[0].click();
    document.querySelectorAll('#shopping-cart a')[0].click();
  }
  addGear = (event) => {
    const gearId = event.target.getAttribute('data-id');
    const data = {
      gear_id: gearId,
      qty: document.getElementById(`gear-oneoff-quantity__${gearId}`).getElementsByTagName('p')[0].innerHTML,
    };
    axios.post('/add-gear/', data)
    .then((response) => {
      let items = this.state.items;
      let needAddition = true;
      items.forEach((item) => {
        if (item.coffee) {
          if (response.data.name === item.coffee.name) {
            item.quantity += response.data.qty;
            needAddition = false;
            return;
          }
        } else if (item.gear) {
          console.log(item.gear, "GEAR");
          if (response.data.name === item.gear.name) {
            item.quantity += response.data.qty;
            needAddition = false;
            return;
          }
        }
      });
      const new_item = {
          gear: {
              id: response.data.gear_id,
              name: response.data.name,
              price: response.data.price,
          },
          quantity: response.data.qty,
      }
      if (needAddition) {
        items.push(new_item, );
      }
      this.syncCart(items);

      fbq('track', "AddToCart", {
        value: response.data.price,
        currency: 'SGD',
        content_name: response.data.name,
        content_type: 'GEAR',
        content_ids: [response.data.gear_id, ],
        contents: new_item
      });
    })
    .catch((error) => {
      console.log(error);
    });
    document.querySelectorAll('.modal.in button.close')[0].click();
    document.querySelectorAll('#shopping-cart a')[0].click();
  }
  addBottled = (event) => {
    const coffeeId = event.target.getAttribute('data-id');
    const data = {
      coffee_id: coffeeId,
      qty: document.getElementById(`pbox-oneoff-quantity__${coffeeId}`).getElementsByTagName('p')[0].innerHTML,
    };
    axios.post('/add-bottled/', data)
    .then((response) => {
      let items = this.state.items;
      let needAddition = true;
      items.forEach((item) => {
        if (item.coffee) {
          if (response.data.name === item.coffee.name &&
            response.data.brew === item.coffee.brew &&
            response.data.package === item.coffee.package) {
            item.quantity += response.data.qty;
            needAddition = false;
            return;
          }
        }
      });
      if (needAddition) {
        items.push(
          { coffee: {
              id: response.data.coffee_id,
              name: response.data.name,
              price: response.data.price,
              brew: response.data.brew,
              brew_id: response.data.brew_id,
              package: response.data.package },
            quantity: response.data.qty,
          },
        );
      }
      this.syncCart(items);
    })
    .catch((error) => {
      console.log(error);
    });
    // close coffee details modal (jQuery off!)
    document.querySelectorAll('.modal.in button.close')[0].click();
    document.querySelectorAll('#shopping-cart a')[0].click();
  }
  syncCart(items) {
    axios.post('/update-cart/', JSON.stringify(items))
    .then((response) => {
      this.setState({
        items: response.data,
      });
    })
    .catch((error) => {
      console.log(error);
    });
  }
  decrease0 = (event) => {
    let node = event.target;
    if (event.target.tagName === 'SPAN') node = node.parentElement;
    let val = parseInt(node.nextElementSibling.innerHTML);
    if (val > 1) val -= 1;
    node.nextElementSibling.innerHTML = val;
  }
  increase0 = (event) => {
    let node = event.target;
    if (event.target.tagName === 'SPAN') node = node.parentElement;
    const val = parseInt(node.previousElementSibling.innerHTML) + 1;
    node.previousElementSibling.innerHTML = val;
  }
  // WARNING: experimental ES7 syntax spotted
  decrease = (order) => {
    let items = this.state.items;
    items.forEach((item) => {
      if (item.coffee) {
        if (item.coffee === order.props.coffee) {
          if (item.quantity > 1) {
            item.quantity -= 1;
          }
          return;
        }
      } else if (item.workshop) {
          if (item.workshop === order.props.coffee) {
            if (item.quantity > 1) {
              console.log(item.quantity);
              item.quantity -= 1;
            }
            return;
          }
      } else {
        if (item.gear === order.props.coffee) {
          if (item.quantity > 1) {
            item.quantity -= 1;
          }
          return;
        }
      }
    });
    this.syncCart(items);
  }
  increase(order) {
    let items = this.state.items;
    items.forEach((item) => {
      if (item.coffee) {
        if (item.coffee === order.props.coffee) {
          item.quantity += 1;
          return;
        }
      } else if (item.workshop) {
          if (item.workshop === order.props.coffee) {
            item.quantity += 1;
            return;
          }
      } else {
        if (item.gear === order.props.coffee) {
          item.quantity += 1;
          return;
        }
      }
    });
    this.syncCart(items);
  }
  delete(order) {
    let items = [];
    this.state.items.forEach((item) => {
      if (item.coffee) {
        if (item.coffee !== order.props.coffee) {
          items.push(item);
          return;
        }
      } else if (item.workshop) {
        if (item.workshop !== order.props.coffee) {
          items.push(item);
          return;
        }
      } else {
        if (item.gear !== order.props.coffee) {
          items.push(item);
          return;
        }
      }
    });
    this.syncCart(items);
  }

  render() {
    return (
      <div className="shopcart-summary">
        <MenuItem count={this.getQuantity()} />
        <ul className="dropdown-menu dropdown-menu-right" aria-labelledby="nav-dd-shopcart">
          <Summary total={this.getSummary()} />
          <OrderList
            items={this.state.items}
            onDecrease={this.decrease}
            onIncrease={this.increase}
            onDelete={this.delete}
          />
          <CheckoutButton len={this.getQuantity()} />
        </ul>
      </div>
    );
  }
}
