// src/api.js

import axios from 'axios';

// 创建一个 Axios 实例，并设置一个基础 URL
// 这个 URL 指向你部署好的 Hugging Face Space 后端
const apiClient = axios.create({
  baseURL: 'https://catnebulaaa-xmulostandfound.hf.space/api', // 重要：使用你自己的 Space 地址，并以 /api 结尾
  // 对于文件上传，通常 axios 会自动设置正确的 Content-Type，所以可以不写
  // headers: {
  //   'Content-Type': 'multipart/form-data'
  // }
});

export default apiClient;