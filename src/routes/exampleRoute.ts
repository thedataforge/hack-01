import { Router, Request, Response } from "express";
import fetchData from "../services/apiService";

const router = Router();

router.get("/data", async (req: Request, res: Response) => {
  try {
    const data = await fetchData();
    res.json(data);
  } catch (error) {
    res.status(500).json({ message: "Error fetching data" });
  }
});

export default router;
