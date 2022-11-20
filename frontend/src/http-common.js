import axios from "axios";

export default axios.create({
    baseURL: "http://localhost:5000/",
    headers: {
        "Content-Type": "application/json",
        Authorization: {
            toString () {
              return `Bearer ${localStorage.getItem('token')}`;
            }
          }
    },
});