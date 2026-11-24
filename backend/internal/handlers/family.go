package handlers

import (
	"ninimenu/internal/database"
	"ninimenu/internal/models"
	"ninimenu/internal/utils"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

// VoteGroup 按菜品聚合的投票
type VoteGroup struct {
	DishID    uint   `json:"dish_id"`
	MemberIDs []uint `json:"member_ids"`
}

type FamilyState struct {
	Members []models.FamilyMember `json:"members"`
	Votes   []VoteGroup           `json:"votes"`
}

// GetFamily 返回成员列表与投票聚合
func GetFamily(c *gin.Context) {
	var members []models.FamilyMember
	database.DB.Order("id").Find(&members)

	var votes []models.DishVote
	database.DB.Order("dish_id").Find(&votes)

	grouped := make(map[uint][]uint)
	order := make([]uint, 0, len(votes))
	for _, v := range votes {
		if _, ok := grouped[v.DishID]; !ok {
			order = append(order, v.DishID)
		}
		grouped[v.DishID] = append(grouped[v.DishID], v.MemberID)
	}
	out := make([]VoteGroup, 0, len(order))
	for _, d := range order {
		out = append(out, VoteGroup{DishID: d, MemberIDs: grouped[d]})
	}
	utils.Success(c, FamilyState{Members: members, Votes: out})
}

type MemberRequest struct {
	Name string `json:"name" binding:"required"`
}

// CreateMember 新增成员（重名直接返回已有）
func CreateMember(c *gin.Context) {
	var req MemberRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		utils.BadRequest(c, "请输入成员名字")
		return
	}
	name := strings.TrimSpace(req.Name)
	if name == "" || len([]rune(name)) > 8 {
		utils.BadRequest(c, "名字需为 1-8 个字")
		return
	}
	m := models.FamilyMember{Name: name}
	if err := database.DB.Where("name = ?", name).FirstOrCreate(&m).Error; err != nil {
		utils.InternalError(c, "保存失败")
		return
	}
	utils.Success(c, m)
}

// DeleteMember 删除成员及其投票
func DeleteMember(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		utils.BadRequest(c, "参数无效")
		return
	}
	database.DB.Where("member_id = ?", id).Delete(&models.DishVote{})
	database.DB.Delete(&models.FamilyMember{}, id)
	utils.SuccessMsg(c, "已删除")
}

type VoteRequest struct {
	MemberID uint `json:"member_id" binding:"required"`
	DishID   uint `json:"dish_id" binding:"required"`
}

// ToggleVote 切换某成员对某道菜的投票
func ToggleVote(c *gin.Context) {
	var req VoteRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		utils.BadRequest(c, "参数无效")
		return
	}
	var existing models.DishVote
	err := database.DB.Where("member_id = ? AND dish_id = ?", req.MemberID, req.DishID).First(&existing).Error
	if err == nil {
		database.DB.Delete(&existing)
		utils.Success(c, gin.H{"voted": false})
		return
	}
	if err != gorm.ErrRecordNotFound {
		utils.InternalError(c, "查询失败")
		return
	}
	if err := database.DB.Create(&models.DishVote{MemberID: req.MemberID, DishID: req.DishID}).Error; err != nil {
		utils.InternalError(c, "保存失败")
		return
	}
	utils.Success(c, gin.H{"voted": true})
}
