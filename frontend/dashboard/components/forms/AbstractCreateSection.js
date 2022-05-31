import React, { useState } from "react";
import { useQueryClient } from "react-query";
import { Formik, Form } from "formik";
import { toast } from "react-toastify";
import Button from "react-bootstrap/Button";
import Modal from "react-bootstrap/Modal";
import Section from "./Section";
import TosurnamentApi from "../../api/TosurnamentApi";

export default function AbstractCreateSection(props) {
  const { id, name, url, data, fields, invalidateQueryKeys } = props;
  const queryClient = useQueryClient();
  const [show, setShow] = useState(false);
  const handleClose = () => {
    setShow(false);
  };
  const handleShow = () => setShow(true);

  let fieldsOfForm = [];
  for (const [fieldName, [fieldType, fieldProps]] of Object.entries(fields)) {
    fieldsOfForm.push(React.createElement(fieldType, { ...props, ...fieldProps, key: fieldName, fieldName }));
  }

  async function onSubmit(values, { setSubmitting, resetForm }) {
    try {
      await TosurnamentApi.post(url, values);
    } catch {
      return;
    } finally {
      setSubmitting(false);
    }
    resetForm({ values });
    toast.success(`${name} created`);
    queryClient.invalidateQueries(invalidateQueryKeys);
    setShow(false);
  }

  return (
    <>
      <Section name={name} id={id}>
        <Button variant="primary" onClick={handleShow} style={{ marginTop: "1em" }}>
          Create
        </Button>
      </Section>
      <Formik initialValues={data} onSubmit={onSubmit} validateOnMount>
        {({ isSubmitting, submitForm }) => (
          <Form>
            <Modal show={show} onHide={handleClose}>
              <Modal.Header closeButton closeVariant="white">
                <Modal.Title>Create {name}</Modal.Title>
              </Modal.Header>
              <Modal.Body>{fieldsOfForm}</Modal.Body>
              <Modal.Footer>
                <Button variant="secondary" onClick={handleClose} disabled={isSubmitting}>
                  Cancel
                </Button>
                <Button variant="primary" type="submit" onClick={submitForm} disabled={isSubmitting}>
                  Create
                </Button>
              </Modal.Footer>
            </Modal>
          </Form>
        )}
      </Formik>
    </>
  );
}
