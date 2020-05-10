# async def test_set_admin_role(self):
#     """Tries to authenticate the user but they didn't link their osu! account yet."""
#     bot_mock = tosurnament_mock.BotMock()
#     bot_mock.session.add_stub(Tournament())
#     cog = tosurnament_mock.mock_cog(guild_owner.get_class(bot_mock))
#     role_mock = mock.Mock()
#     role_mock.id = 0

#     await cog.set_admin_role(
#         cog, tosurnament_mock.CtxMock(bot_mock), role=role_mock
#     )
#     assert bot_mock.session.update.call_count == 1
#     cog.send_reply.assert_called_with(mock.ANY, "success")
