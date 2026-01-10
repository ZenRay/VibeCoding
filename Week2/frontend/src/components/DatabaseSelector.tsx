/** 数据库选择器组件 */
import React from "react";
import { Select } from "antd";
import { DatabaseConnectionResponse } from "../types/database";

interface DatabaseSelectorProps {
  databases: DatabaseConnectionResponse[];
  value?: string;
  onChange?: (name: string) => void;
  placeholder?: string;
}

const DatabaseSelector: React.FC<DatabaseSelectorProps> = ({
  databases,
  value,
  onChange,
  placeholder = "选择数据库",
}) => {
  return (
    <Select
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      style={{ width: "100%" }}
      options={databases.map((db) => ({
        label: `${db.name} (${db.dbType})`,
        value: db.name,
      }))}
    />
  );
};

export default DatabaseSelector;
