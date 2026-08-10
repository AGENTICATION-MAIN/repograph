import axios from 'axios';

export async function fetchUsers() {
    const res = await axios.get('http://localhost:8080/users');
    return res.data;
}
