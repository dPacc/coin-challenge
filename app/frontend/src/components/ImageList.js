import React, { useEffect, useState } from "react";
import {
  List,
  Spin,
  Modal,
  Button,
  message,
  Card,
  Row,
  Col,
  Typography,
} from "antd";
import axios from "axios";

const { Title, Text } = Typography;

const ImageList = () => {
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [objects, setObjects] = useState([]);
  const [selectedObject, setSelectedObject] = useState(null);
  const [objectDetailsLoading, setObjectDetailsLoading] = useState(false);

  useEffect(() => {
    fetchImages();
  }, []);

  const fetchImages = async () => {
    setLoading(true);
    try {
      const result = await axios("http://localhost:8000/images");
      setImages(result.data);
    } catch (error) {
      message.error("Failed to fetch images");
    } finally {
      setLoading(false);
    }
  };

  const handleImageClick = (image) => {
    setSelectedImage(image);
    setObjects([]);
    setSelectedObject(null);
    setIsModalOpen(true);
  };

  const fetchObjects = async (imageId) => {
    try {
      const result = await axios(`http://localhost:8000/objects/${imageId}`);
      setObjects(result.data);
    } catch (error) {
      message.error("Failed to fetch object details");
    }
  };

  const handleObjectClick = async (objectId) => {
    setObjectDetailsLoading(true);
    try {
      const result = await axios(`http://localhost:8000/object/${objectId}`);
      setSelectedObject(result.data);
    } catch (error) {
      message.error("Error fetching object details");
    } finally {
      setObjectDetailsLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: "100%", overflow: "auto" }}>
      <Title level={2}>Uploaded Images</Title>
      {loading ? (
        <Spin
          size="large"
          style={{ display: "flex", justifyContent: "center", marginTop: 20 }}
        />
      ) : (
        <List
          grid={{
            gutter: 16,
            xs: 1,
            sm: 2,
            md: 3,
            lg: 4,
            xl: 4,
            xxl: 4,
          }}
          dataSource={images}
          renderItem={(item) => (
            <List.Item>
              <Card
                hoverable
                cover={
                  <img
                    alt={item.filename}
                    src={`data:image/png;base64,${item.data}`}
                    style={{ maxHeight: 200, objectFit: "cover" }}
                  />
                }
                actions={[
                  <Button key="view" onClick={() => handleImageClick(item)}>
                    View Details
                  </Button>,
                  <Button key="delete" type="danger">
                    Delete Image
                  </Button>,
                ]}
              >
                <Card.Meta
                  title={item.filename}
                  description="Click 'View Details' to see more or 'Delete Image' to remove."
                />
              </Card>
            </List.Item>
          )}
        />
      )}

      <Modal
        title={`Details for ${selectedImage?.filename}`}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={null}
        width={800}
      >
        <img
          alt={selectedImage?.filename}
          src={`data:image/jpeg;base64,${selectedImage?.data}`}
          style={{ width: "100%", maxHeight: "200px", objectFit: "contain" }}
        />
        <Row gutter={16} style={{ marginTop: 16 }}>
          <Col span={12} style={{ overflow: "auto", maxHeight: 300 }}>
            <Title level={4}>Circular Objects</Title>
            <Button onClick={() => fetchObjects(selectedImage.id)}>
              Retrieve Objects
            </Button>
            {objects.length > 0 && (
              <List
                itemLayout="horizontal"
                dataSource={objects}
                renderItem={(item) => (
                  <List.Item
                    actions={[
                      <Button onClick={() => handleObjectClick(item.id)}>
                        View Details
                      </Button>,
                    ]}
                  >
                    <List.Item.Meta
                      title={`Object ID: ${item.id}`}
                      description={`Bounding Box: ${JSON.stringify(item.bbox)}`}
                    />
                  </List.Item>
                )}
              />
            )}
          </Col>
          <Col span={12}>
            {objectDetailsLoading ? (
              <Spin
                size="large"
                style={{
                  display: "flex",
                  justifyContent: "center",
                  marginTop: 20,
                }}
              />
            ) : selectedObject ? (
              <div>
                <Title level={5}>Details of Selected Object</Title>
                <p>Object ID: {selectedObject.id}</p>
                <p>Bounding Box: {JSON.stringify(selectedObject.bbox)}</p>
                <p>Centroid: {JSON.stringify(selectedObject.centroid)}</p>
                <p>Radius: {selectedObject.radius}</p>
              </div>
            ) : (
              <Text type="secondary">Select an object to view details.</Text>
            )}
          </Col>
        </Row>
      </Modal>
    </div>
  );
};

export default ImageList;
