/** 元数据刷新提示横幅组件 */
import React from "react";
import { Alert, Button, Space } from "antd";
import { ReloadOutlined } from "@ant-design/icons";

interface MetadataRefreshBannerProps {
  visible: boolean;
  onRefresh: () => void;
}

const MetadataRefreshBanner: React.FC<MetadataRefreshBannerProps> = ({
  visible,
  onRefresh,
}) => {
  if (!visible) {
    return null;
  }

  return (
    <Alert
      message="数据库结构已更改"
      description="建议刷新元数据以获取最新信息"
      type="info"
      showIcon
      action={
        <Button size="small" icon={<ReloadOutlined />} onClick={onRefresh}>
          刷新
        </Button>
      }
      closable
      style={{ marginBottom: 16 }}
    />
  );
};

export default MetadataRefreshBanner;
