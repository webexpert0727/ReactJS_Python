import React from 'react';
import {
  BrowserRouter as Router,
  Route,
  Redirect,
  Switch,
} from 'react-router-dom';

import {
  DashboardPage,
  PackingPage,
  CustomersPage,
  MarketingPage,
  InventoryPage,
  CoffeeDemandPage,
  CustomerSegmentationPage,
} from './components';
import {
  App,
  LoginPage,
} from './containers';
import { Auth } from './utils';
import { ManagerRole } from './constants';


const ProtectedRoute = ({ component: Component, requireRole, ...rest }) => (
  // eslint-disable-next-line
  <Route {...rest} render={props => Auth.hasPerms(requireRole)
    ? <Component {...props} />
    : <Redirect to={{ pathname: '/', state: { from: props.location } }} />}
  />
);


const Routes = () => (
  <Router basename="/manager">
    <App>
      <Switch>
        <Route exact path="/" component={LoginPage} />
        <ProtectedRoute path="/dashboard" component={DashboardPage} requireRole={ManagerRole.ADMIN} />
        <ProtectedRoute path="/marketing" component={MarketingPage} requireRole={ManagerRole.ADMIN} />
        <ProtectedRoute path="/demand" component={CoffeeDemandPage} requireRole={ManagerRole.ADMIN} />
        <ProtectedRoute path="/segmentation" component={CustomerSegmentationPage} requireRole={ManagerRole.ADMIN} />
        <ProtectedRoute path="/packing" component={PackingPage} requireRole={ManagerRole.PACKER} />
        <ProtectedRoute path="/customers" component={CustomersPage} requireRole={ManagerRole.PACKER} />
        <ProtectedRoute path="/inventory" component={InventoryPage} requireRole={ManagerRole.PACKER} />
      </Switch>
    </App>
  </Router>
);


export default Routes;
