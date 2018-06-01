import React from 'react';
import styles from './Loading.css';

export default () => (
  <div className={styles.loading}>
    <i className="fa fa-spinner fa-spin fa-3x" />
  </div>
);
