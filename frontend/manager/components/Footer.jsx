import React from 'react';


export default () => (
  <section className="footer" style={{ height: '140px' }}>
    <div className="container">
      <div className="row text-center">
        <div className="col-xs-12">
          <div className="footer-content">
            <img className="footer-logo" src={`${STATIC}images/site-logo-light.png`} alt="HookCoffee" />
            <h4>The freshest coffee you&apos;ll ever make</h4>
            <p><small><a><i className="fa fa-copyright" />HOOK COFFEE</a></small></p>
          </div>
        </div>
      </div>
    </div>
  </section>
);
