import axios, { CancelToken } from 'axios';

axios.defaults.baseURL = '/manager/api/';
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';


export default class ApiRequest {

  constructor(method, url, data, config) {
    // axios.defaults.paramsSerializer = () => querystring.stringify(params);
    if (typeof data.params !== 'undefined') {
      const params = data.params;
      return axios({ method, url, params });
    }
    return axios({ method, url, data, ...config });
  }

  static getCancelTokenSource = () => new CancelToken.source();

  static get = (url, params = {}) => new ApiRequest('get', url, { params });

  static post = (url, data = {}, config = {}) => (
    new ApiRequest('post', url, data, config)
  )

}
