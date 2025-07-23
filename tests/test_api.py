def test_create_batch(client, test_batch_data):
    """Тест правильной обработки создания задания"""

    response = client.post(
        "/add_batch/",
        json=test_batch_data,
    )

    if response.status_code != 200:
        print("Error details:", response.json())

    assert response.status_code == 200
    data = response.json()
    assert data["batch_number"] == 3


def test_get_batch_id(client):
    """Тест правильной обработки получения задания"""

    response = client.get("/get_batch/", params={"batch_id": 1})

    assert response.status_code == 200


def test_create_product(client, test_batch_data, test_product_data):
    """Тест правильной обработки создания продукта"""

    product_response = client.post("/add_product/", json=test_product_data)
    assert product_response.status_code == 200
