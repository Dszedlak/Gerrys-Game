import axios from "axios";
import { IP_ADDRESS, BACKEND_PORT, BACKEND_PROTOCOL } from "@/common/config";

const ipAddress = IP_ADDRESS;
const port = BACKEND_PORT;
const protocol = BACKEND_PROTOCOL;

export default axios.create({
  
    baseURL: `${protocol}://${ipAddress}:${port}/`,
    headers: {
        "Content-Type": "application/json",
        Authorization: {
            toString () {
              return `Bearer ${localStorage.getItem('token')}`;
            }
          }
    },
});