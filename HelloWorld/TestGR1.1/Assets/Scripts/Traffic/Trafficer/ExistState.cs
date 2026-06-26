/// <summary>
/// Trạng thái điều khiển / vòng đời của một trafficer.
/// Giá trị số: 0=hủy, 1=server, 2=client, 3=xác xe — khớp field "e" trong UnityVehicleData.
/// Đồng bộ với phía server (field "e" trong UnityVehicleData).
/// </summary>
public enum ExistState
{
	/// <summary>Hủy, hết vòng đời → server remove khỏi SUMO, Unity recycle.</summary>
	Destroyed = 0,
	/// <summary>Đang tồn tại, được điều khiển bởi server (xe SUMO bình thường).</summary>
	ServerControlled = 1,
	/// <summary>Đang tồn tại, được điều khiển bởi client (lái tay, vật lý). Server mirror theo.</summary>
	ClientControlled = 2,
	/// <summary>Xác xe sau va chạm: vật lý, không ai lái; SUMO đông cứng gây ùn ứ; tự hủy sau N bước.</summary>
	Wrecked = 3
}
