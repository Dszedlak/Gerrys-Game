import axios from "axios";
import { IP_ADDRESS } from "@/common/config";

const ipAddress = IP_ADDRESS;

export default axios.create({
  
    baseURL: `http://${ipAddress}:5000/`,
    headers: {
        "Content-Type": "application/json",
        Authorization: {
            toString () {
              return `Bearer ${localStorage.getItem('token')}`;
            }
          }
    },
});