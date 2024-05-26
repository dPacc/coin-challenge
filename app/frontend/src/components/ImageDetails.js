import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import { Card } from "antd";

const ImageDetails = () => {
  const [image, setImage] = useState(null);
  const { id } = useParams();

  useEffect(() => {
    const fetchImage = async () => {
      const result = await axios(`http://localhost:8000/image/${id}`);
      setImage(result.data);
    };

    fetchImage();
  }, [id]);

  return image ? (
    <Card
      hoverable
      style={{ width: 240 }}
      cover={
        <img
          alt={image.filename}
          src={`data:image/jpeg;base64,${image.data}`}
        />
      }
    >
      <Card.Meta title={image.filename} description={`ID: ${image.id}`} />
    </Card>
  ) : null;
};

export default ImageDetails;
