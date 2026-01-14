import qz from "qz-tray";

const API_URL = process.env.REACT_APP_API_URL

// ====== 1️⃣ Load certificate from Django ======
qz.security.setCertificatePromise((resolve, reject) => {
  fetch('${API_URL}/qz/certificate/')  // Adjust domain
    .then((res) => res.text())
    .then(resolve)
    .catch(reject);
});

// ====== 2️⃣ Secure digital signature via Django ======
qz.security.setSignaturePromise((toSign) => {
  return (resolve, reject) => {
    fetch(`${API_URL}/qz/sign/?data=${toSign}`)
      .then((res) => res.json())
      .then((data) => resolve(data.signature))
      .catch((err) => reject(err));
  };
});

// ====== 3️⃣ Print helper ======
export const printReceipt = async (receiptText) => {
  try {
    await qz.websocket.connect();

    let config = qz.configs.create(null, {
      size: { width: 72, height: null },
      density: "600",
      charset: "utf-8",
      end: "\n\n\n"
    });

    await qz.print(config, [{ type: "raw", format: "plain", data: receiptText }]);
    console.log("Printed Successfully");
  } catch (err) {
    console.error(err);
  }
};
