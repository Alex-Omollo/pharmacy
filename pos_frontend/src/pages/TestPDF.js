
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';

const TestPDF = () => {
  const generatePDF = () => {
    const doc = new jsPDF();
    autoTable(doc, {
      head: [['Name', 'Age']],
      body: [
        ['John Doe', '29'],
        ['Jane Smith', '34'],
      ],
    });
    doc.save('test.pdf');
  };

  return <button onClick={generatePDF}>Test PDF</button>;
};

export default TestPDF;
