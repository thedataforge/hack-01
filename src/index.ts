import express from "express";
import bodyParser from "body-parser";
import cors from "cors";
import { transferRoute } from "./routes/transfer";

const app = express();
const PORT = 4000;

// Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static("public"));

// Route - using POST method
app.post("/api/transfer", transferRoute);
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
