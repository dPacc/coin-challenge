import React, { useState } from "react";
import axios from "axios";
import { Button, message, Select, Table, Row, Col, Modal, Card } from "antd";

const { Option } = Select;

const UploadImage = () => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [objects, setObjects] = useState([]);
  const [selectedAlgorithm, setSelectedAlgorithm] = useState("manual");
  const [originalImage, setOriginalImage] = useState(null);
  const [bboxImage, setBboxImage] = useState(null);
  const [maskedImage, setMaskedImage] = useState(null);
  // Modal States
  const [modalVisible, setModalVisible] = useState(false);
  const [modalImage, setModalImage] = useState(null);

  const handleImageUpload = async (sampleImage = null) => {
    if (!selectedImage && !sampleImage) {
      message.error("Please select an image first!");
      return;
    }

    const formData = new FormData();
    if (selectedImage) {
      formData.append("image", selectedImage);
    } else {
      const response = await fetch(sampleImage);
      const blob = await response.blob();
      const fileName = sampleImage.split("/").pop();
      const file = new File([blob], fileName, { type: "image/jpeg" });
      formData.append("image", file);
    }

    setUploading(true);

    try {
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL}/upload`,
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );
      message.success("Image uploaded successfully");
      processImage(response.data.id);
    } catch (error) {
      message.error("Error uploading image");
      console.error("Error uploading image:", error);
    } finally {
      setUploading(false);
    }
  };

  const processImage = async (imageId) => {
    setProcessing(true);
    try {
      const response = await axios.post(
        `${process.env.REACT_APP_API_URL}/process/${imageId}`,
        { algorithm: selectedAlgorithm }
      );
      setObjects(response.data.objects);
      setOriginalImage(
        `data:image/jpeg;base64,${response.data.original_image}`
      );
      setBboxImage(`data:image/jpeg;base64,${response.data.bbox_image}`);
      setMaskedImage(`data:image/jpeg;base64,${response.data.masked_image}`);
      message.success("Image processed successfully");
    } catch (error) {
      message.error("Error processing image");
      console.error("Error processing image:", error);
    } finally {
      setProcessing(false);
    }
  };

  const handleImageClick = (image) => {
    setModalImage(image);
    setModalVisible(true);
  };

  const columns = [
    {
      title: "ID",
      dataIndex: "id",
      key: "id",
    },
    {
      title: "Bounding Box",
      dataIndex: "bbox",
      key: "bbox",
      render: (bbox) => JSON.stringify(bbox),
    },
    {
      title: "Centroid",
      dataIndex: "centroid",
      key: "centroid",
      render: (centroid) => JSON.stringify(centroid),
    },
    {
      title: "Radius",
      dataIndex: "radius",
      key: "radius",
    },
  ];

  return (
    <div
      style={{
        maxWidth: "100%",
        overflow: "auto",
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          marginTop: 16,
          marginBottom: 32,
        }}
      >
        <Row justify="center" style={{ width: "100%" }}>
          <h1>Circular Object Segmentation</h1>
        </Row>

        <Row justify="center" style={{ width: "100%" }}>
          <input
            type="file"
            onChange={(e) => setSelectedImage(e.target.files[0])}
            style={{ marginRight: 16 }}
          />
          <Select
            value={selectedAlgorithm}
            onChange={(value) => setSelectedAlgorithm(value)}
            style={{ width: 200, marginRight: 16 }}
          >
            <Option value="manual">Manual</Option>
            <Option value="hough">Hough Transform</Option>
            <Option value="contour">Contour</Option>
          </Select>
          <Button
            onClick={handleImageUpload}
            loading={uploading || processing}
            type="primary"
            disabled={!selectedImage}
          >
            Upload and Process Image
          </Button>
        </Row>
      </div>

      {originalImage && bboxImage && maskedImage && (
        <Row gutter={16} style={{ marginTop: 16 }}>
          <Col span={8}>
            <Card title="Original Image">
              <img
                src={originalImage}
                alt="Original"
                style={{ maxWidth: "400px", height: "auto", cursor: "pointer" }}
                onClick={() => handleImageClick(originalImage)}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card title="Image with Bounding Boxes & Unique Identifier (number)">
              <img
                src={bboxImage}
                alt="Bounding Boxes"
                style={{ maxWidth: "400px", height: "auto", cursor: "pointer" }}
                onClick={() => handleImageClick(bboxImage)}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card title="Masked Image">
              <img
                src={maskedImage}
                alt="Masked"
                style={{ maxWidth: "400px", height: "auto", cursor: "pointer" }}
                onClick={() => handleImageClick(maskedImage)}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Modal
        visible={modalVisible}
        footer={null}
        onCancel={() => setModalVisible(false)}
      >
        <img src={modalImage} alt="Enlarged" style={{ width: "100%" }} />
      </Modal>

      {objects.length > 0 && (
        <Card title="Detected Objects" style={{ marginTop: 16 }}>
          <Table dataSource={objects} columns={columns} rowKey="id" />
        </Card>
      )}
    </div>
  );
};

export default UploadImage;
