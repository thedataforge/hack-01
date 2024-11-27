import { UnifiedTo } from "@unified-api/typescript-sdk";
import axios from "axios";
import fs from "fs"; 

export async function transferRoute(req: any, res: any) {
  console.log(req.body);
  const formData = req.body;
  const fromConnectionId = formData.fromConnectionId;
  const toConnectionId = formData.toConnectionId;

  const sdk = new UnifiedTo({
    security: {
      jwt: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2NzA4MGViZjdkOGY2MDYxNzhlNDIxNDYiLCJ3b3Jrc3BhY2VfaWQiOiI1ZThiYTExZDNmYjhmZjk1YzkwYjczMzIiLCJpYXQiOjE3Mjg1ODEzMTF9.vDN99Z1olKzYJkgQeVWJGrj05T-e6WMFL8KVdz_es2s",
    },
  });
  const apiResponse: any = await sdk.accounting.listAccountingAccounts({
    connectionId: fromConnectionId,
  });
  console.log("reached here");
  const listOfAccountsFailed = [];
  for (const account of apiResponse) {
    console.log("reached here 2");
    try{
      var apiCreateResponse: any = await sdk.accounting.createAccountingAccount(
        {
        connectionId: toConnectionId,
        accountingAccount: account,
      }
      );
    } catch (error) {
      console.log("Account creation failed for account ", account.id);
      listOfAccountsFailed.push(account.id);
    }
    if (apiCreateResponse?.statusCode == 200) {
      console.log("Account created successfully");
    } else {
      console.log("Account creation failed for account ", account.id);
      try {
        const response = await axios.post(
          "https://api.notificationapi.com/jwe5suu1nyn7qsnm0wu7lv2wsm/sender",
          {
            notificationId: "id_crashed",
            user: {
              id: "vaibhav@unified.to",
              email: "vaibhav@unified.to",
              number: "+15005550006",
            },
            mergeTags: {
              comment: "testComment",
              commentId: "testCommentId",
            },
          },
          {
            headers: {
              Authorization:
                "Basic andlNXN1dTFueW43cXNubTB3dTdsdjJ3c206N3BlNnY1NHN1cWk1cTN2Z2pieDY1dHIwdzBucGRkNjJmaDdjNHd6dHNicHNmaHV4Y3VvZDVudmM5bA==",
              "Content-Type": "application/json",
            },
          }
        );

        console.log("Notification sent successfully");
      } catch (error) {
        console.error("Failed to send notification:", error);
      }
      console.log("Account creation failed for account ", account.id);
    }
  }
  if (listOfAccountsFailed.length > 0) {
    const jsonData = JSON.stringify(listOfAccountsFailed);

    // Write the JSON data to a file on localhost
    fs.writeFile("failed_accounts.json", jsonData, (err) => {
      if (err) {
        console.error("Failed to write JSON file:", err);
      } else {
        console.log("JSON file saved successfully");
      }
    });
    res.json({
      listOfAccountsFailed: listOfAccountsFailed,
    });
  }
  if (apiResponse?.statusCode == 200) {
    res.json({
      accountingAccounts: apiResponse?.accountingAccounts,
    });
  } else {
    res.status(apiResponse?.statusCode || 500).json({
      error: "Failed to fetch accounting accounts",
    });
  }
}
