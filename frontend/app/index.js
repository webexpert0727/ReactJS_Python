import React from 'react';
import ReactDOM from 'react-dom';
// import { AppContainer } from 'react-hot-loader';

import { ShoppingCart } from './components';

// const render = (Component) => {
//   ReactDOM.render(
//     <AppContainer>
//       <Component />
//     </AppContainer>,
//     document.getElementById('')
//   );
// };

// temporary solution
const shoppingCart = document.getElementById('shopping-cart');
if (shoppingCart) {
  ReactDOM.render(<ShoppingCart />, shoppingCart);
}

// if (module.hot) {
//   module.hot.accept();
// }
