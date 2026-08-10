import express from 'express';
import { fetchUsers } from './api';

const app = express();
app.get('/users', async (req, res) => {
    const data = await fetchUsers();
    res.json(data);
});
